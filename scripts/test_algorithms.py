#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import socket
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http.client import HTTPConnection, HTTPResponse
from urllib.parse import urlparse

PROXY_URL: str = "http://127.0.0.1:8080"
HOST: str = urlparse(PROXY_URL).hostname
PROXY_PORT: int = urlparse(PROXY_URL).port

INTERNAL_URL: str = "http://127.0.0.1:9090"
INTERNAL_PORT: int = urlparse(INTERNAL_URL).port

PATH: str = "/"
TIMEOUT_SECONDS: float = 5

UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)


def extract_backend_id(body: bytes) -> str | None:
    match = UUID_RE.search(body.decode("utf-8", errors="ignore"))
    return match.group(0) if match else None


def short_id(backend: str | None) -> str:
    """Full UUIDs are hard to visually compare; show a short, distinct tail."""
    if not backend:
        return "UNKNOWN"
    return backend[-8:] if len(backend) > 8 else backend


def banner(title: str) -> None:
    line = "=" * 70
    print(f"\n{line}\n {title}\n{line}")


def section(title: str) -> None:
    print(f"\n-- {title} --")


def bar_chart(counts: dict[str, int], width: int = 30) -> None:
    if not counts:
        print("  (no data)")
        return
    max_count = max(counts.values()) or 1
    for key in sorted(counts):
        count = counts[key]
        filled = round((count / max_count) * width)
        bar = "#" * filled + "." * (width - filled)
        print(f"  {key:<10} [{bar}] {count}")


def verdict(label: str, passed: bool) -> None:
    status = "PASS" if passed else "FAIL"
    print(f"\n  RESULT: {label} -> {status}")


def get_settings() -> dict:
    conn = HTTPConnection(HOST, INTERNAL_PORT, timeout=TIMEOUT_SECONDS)
    try:
        conn.request("GET", "/settings", headers={"Connection": "close"})
        resp = conn.getresponse()
        body = resp.read()
        if resp.status != 200:
            raise RuntimeError(f"GET /settings returned {resp.status}: {body!r}")
        return json.loads(body)
    finally:
        conn.close()


def post_reload(config: dict) -> None:
    conn = HTTPConnection(HOST, INTERNAL_PORT, timeout=TIMEOUT_SECONDS)
    try:
        payload = json.dumps(config).encode("utf-8")
        conn.request(
            "POST", "/reload", body=payload,
            headers={"Connection": "close", "Content-Type": "application/json"}
        )
        resp = conn.getresponse()
        body = resp.read()
        if resp.status not in (200, 204):
            raise RuntimeError(f"POST /reload returned {resp.status}: {body!r}")
    finally:
        conn.close()


def build_override_config(base_config: dict, algorithm: str, weights: list[int] | None) -> dict:
    override = json.loads(json.dumps(base_config))  # deep copy
    override["algorithm_strategy"] = algorithm
    if weights:
        targets = override["targets"]
        if len(weights) != len(targets):
            raise ValueError(
                f"--weights has {len(weights)} values but config has {len(targets)} targets"
            )
        for target, weight in zip(targets, weights):
            target["weight"] = weight
    return override


class SourceBoundHTTPConnection(HTTPConnection):
    def __init__(self, host: str, port: int, source_ip: str | None, timeout: float) -> None:
        super().__init__(host, port, timeout=timeout)
        self._source_ip = source_ip

    def connect(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        if self._source_ip is not None:
            sock.bind((self._source_ip, 0))
        sock.connect((self.host, self.port))
        self.sock = sock


@dataclass
class RequestResult:
    ok: bool
    backend: str | None
    response_time: float
    error: str | None = None


def do_request(source_ip: str | None = None, path: str = PATH) -> RequestResult:
    started = time.perf_counter()
    conn = SourceBoundHTTPConnection(HOST, PROXY_PORT, source_ip, TIMEOUT_SECONDS)
    try:
        conn.request("GET", path, headers={"Connection": "close"})
        resp: HTTPResponse = conn.getresponse()
        body = resp.read()
        backend = extract_backend_id(body)
        elapsed = time.perf_counter() - started
        return RequestResult(ok=True, backend=backend, response_time=elapsed)
    except Exception as e:
        return RequestResult(ok=False, backend=None, response_time=time.perf_counter() - started, error=str(e))
    finally:
        conn.close()


def print_distribution(results: list[RequestResult], label: str) -> Counter[str]:
    dist: Counter[str] = Counter(short_id(r.backend) for r in results if r.ok)
    failures = [r for r in results if not r.ok]

    section(f"{label} ({len(results)} requests)")
    bar_chart(dist)
    if failures:
        error_counts = Counter(f.error for f in failures)
        print(f"  failures: {len(failures)}")
        for error, count in sorted(error_counts.items()):
            print(f"    - {error}: {count}")
    return dist


def test_round_robin(n: int = 20) -> None:
    banner("ROUND ROBIN")
    results = [do_request() for _ in range(n)]
    dist = print_distribution(results, "Distribution")

    ok_results = [r for r in results if r.ok]
    sequence = [short_id(r.backend) for r in ok_results]
    section("Order seen")
    print(f"  {' -> '.join(sequence)}")

    if len(dist) < 2:
        print("\n  WARNING: only one backend was hit. Check target count or backend extraction.")
        verdict("Round Robin", False)
        return

    expected = n / len(dist)
    skew = max(abs(c - expected) for c in dist.values())
    section("Balance check")
    print(f"  Expected ~{expected:.1f} Requests/backend, max skew={skew:.1f}")
    verdict("Round Robin", skew <= expected * 0.5)


def test_sticky_round_robin(clients: int = 4, requests_per_client: int = 5) -> None:
    banner("STICKY ROUND ROBIN")
    client_ips = [f"127.0.0.{i + 1}" for i in range(clients)]
    per_client_backends: dict[str, list[str]] = {}

    section("Per-client request sequence")
    for ip in client_ips:
        results = [do_request(source_ip=ip) for _ in range(requests_per_client)]
        backends = [short_id(r.backend) if r.ok else f"ERR:{r.error}" for r in results]
        per_client_backends[ip] = backends
        print(f"  {ip:<14} {' -> '.join(backends)}")

    section("Stickiness check")
    all_sticky = True
    for ip, backends in per_client_backends.items():
        distinct = set(backends)
        status = "stuck" if len(distinct) == 1 else "DRIFTED"
        print(f"  {ip:<14} {status:<8} {sorted(distinct)}")
        if len(distinct) > 1:
            all_sticky = False

    first_contacts = [backends[0] for backends in per_client_backends.values()]
    distinct_first = len(set(first_contacts))
    section("First-contact spread")
    print(f"  Distinct backends on first contact: {distinct_first} (expect > 1 if clients <= target count)")
    verdict("Sticky Round Robin", all_sticky)


def test_weighted_round_robin(n: int = 70, weights: list[int] | None = None) -> None:
    banner("WEIGHTED ROUND ROBIN")
    results = [do_request() for _ in range(n)]
    dist = print_distribution(results, "distribution")

    if not weights:
        print("\n  (no weights available to compare against; check config targets)")
        return

    total_weight = sum(weights)
    total_ok = sum(dist.values())
    backends_sorted = sorted(dist.items())

    section("Observed vs Expected share")
    max_diff = 0.0
    for (backend, count), weight in zip(backends_sorted, weights):
        observed_share = count / total_ok if total_ok else 0
        expected_share = weight / total_weight
        diff = abs(observed_share - expected_share)
        max_diff = max(max_diff, diff)
        print(f"  {backend:<10} weight={weight:<3} observed={observed_share:>7.2%}  expected={expected_share:>7.2%}")

    verdict("Weighted Round Robin", max_diff <= 0.10)


def test_ip_hash(clients: int = 4, requests_per_client: int = 5) -> None:
    banner("IP HASH")
    client_ips = [f"127.0.0.{i + 1}" for i in range(clients)]
    all_consistent = True

    section("Per-client mapping")
    for ip in client_ips:
        results = [do_request(source_ip=ip) for _ in range(requests_per_client)]
        backends = [short_id(r.backend) if r.ok else f"ERR:{r.error}" for r in results]
        distinct = set(backends)
        status = "Consistent" if len(distinct) == 1 else "INCONSISTENT"
        print(f"  {ip:<14} {status:<14} {' -> '.join(backends)}")
        if len(distinct) > 1:
            all_consistent = False

    verdict("IP Hash", all_consistent)


def test_least_connections(concurrency: int = 20) -> None:
    banner("LEAST CONNECTIONS")

    results: list[RequestResult] = []
    lock = threading.Lock()

    barrier = threading.Barrier(concurrency)

    def fire() -> None:
        barrier.wait()  # all threads released together

        r = do_request()

        with lock:
            results.append(r)

    threads = [
        threading.Thread(target=fire)
        for _ in range(concurrency)
    ]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    dist = print_distribution(results, "concurrent burst")

    verdict("least_connections", len(dist) >= 2)


def test_least_response_time(warmup_requests: int = 10, followup_requests: int = 20) -> None:
    banner("LEAST RESPONSE TIME")
    print(f"  Warming up stats with {warmup_requests} sequential requests...")
    warmup = [do_request() for _ in range(warmup_requests)]
    print_distribution(warmup, "warmup phase")

    print(f"\n  Running {followup_requests} follow-up requests, expecting bias toward faster backend(s)...")
    followup = [do_request() for _ in range(followup_requests)]
    dist = print_distribution(followup, "follow-up phase")

    section("Interpretation")
    if len(dist) == 1:
        winner = next(iter(dist))
        print(f"  All follow-up requests went to {winner}: consistent with it being measurably faster.")
    else:
        print("  Mixed distribution: backends may have similar latency, or this needs more samples.")
    print("  (No automatic pass/fail here -- compare against your backends' actual relative latency)")


ALGORITHM_TESTS = {
    "round_robin": lambda args, weights: test_round_robin(n=args.requests or 21),
    "sticky_round_robin": lambda args, weights: test_sticky_round_robin(
        clients=args.clients or 4, requests_per_client=args.requests or 5
    ),
    "weighted_round_robin": lambda args, weights: test_weighted_round_robin(
        n=args.requests or 70, weights=weights
    ),
    "ip_hash": lambda args, weights: test_ip_hash(clients=args.clients or 4, requests_per_client=args.requests or 5),
    "least_connections": lambda args, weights: test_least_connections(
        concurrency=args.concurrency or 20
    ),
    "least_response_time": lambda args, weights: test_least_response_time(
        warmup_requests=args.requests or 10, followup_requests=args.followup or 20
    ),
}


def run_algorithm_test(algorithm: str, args: argparse.Namespace) -> None:
    """
    Switches the live load balancer into `algorithm` via /reload (preserving
    the originally configured targets, only overriding algorithm_strategy
    and, optionally, weights), runs the matching test, then always restores
    the original config afterward -- even if the test raises.
    """
    original_config = get_settings()
    override_config = build_override_config(original_config, algorithm, args.weights)

    print(f"\n>>> Reloading load balancer into algorithm_strategy={algorithm!r}")
    post_reload(override_config)

    try:
        effective_weights = [t["weight"] for t in override_config["targets"]]
        ALGORITHM_TESTS[algorithm](args, effective_weights)
    finally:
        print(f"\n<<< Restoring original config (algorithm_strategy={original_config['algorithm_strategy']!r})")
        post_reload(original_config)


def main() -> None:
    parser = argparse.ArgumentParser(description="Test load balancing algorithms against a live load balancer")
    parser.add_argument("algorithm", choices=[*ALGORITHM_TESTS.keys(), "all"])
    parser.add_argument("--requests", type=int, default=None, help="number of requests for sequential tests")
    parser.add_argument("--clients", type=int, default=None, help="number of distinct client IPs to simulate")
    parser.add_argument("--concurrency", type=int, default=None, help="concurrent workers for least_connections")
    parser.add_argument("--followup", type=int, default=None, help="follow-up request count for least_response_time")
    parser.add_argument(
        "--weights", type=lambda s: [int(x) for x in s.split(",")], default=None,
        help="comma-separated weights to push to targets via /reload, e.g. 1,2,4 (order matches config targets)"
    )
    args = parser.parse_args()

    if args.algorithm == "all":
        for name in ALGORITHM_TESTS:
            try:
                run_algorithm_test(name, args)
            except Exception as e:
                print(f"\n=== {name} === FAILED TO RUN: {e}")
            time.sleep(1)
    else:
        run_algorithm_test(args.algorithm, args)


if __name__ == "__main__":
    main()