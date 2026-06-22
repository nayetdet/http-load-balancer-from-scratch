#!/usr/bin/env python3
from __future__ import annotations

import signal
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from http.client import HTTPConnection

URL: str = "http://127.0.0.1:30080"
PATH: str = "/"
CONCURRENCY: int = 32
DURATION_SECONDS: float = 120
TIMEOUT_SECONDS: float = 5

def worker(stop: threading.Event, lock: threading.Lock, stats: Counter[str]) -> None:
    while not stop.is_set():
        conn = HTTPConnection("127.0.0.1", 30080, timeout=TIMEOUT_SECONDS)
        try:
            conn.request("GET", PATH, headers={"Connection": "close"})
            conn.getresponse().read()
            with lock:
                stats["ok"] += 1
        except Exception as e:
            with lock:
                stats[type(e).__name__] += 1
            time.sleep(0.05)
        finally:
            conn.close()

def main() -> None:
    stop: threading.Event = threading.Event()
    lock: threading.Lock = threading.Lock()
    stats: Counter[str] = Counter()

    def stop_now(*_: object) -> None:
        print("\n[stop] stopping...", flush=True)
        stop.set()

    signal.signal(signal.SIGINT, stop_now)
    signal.signal(signal.SIGTERM, stop_now)
    print(f"[run] {URL}{PATH} x{CONCURRENCY} for {DURATION_SECONDS}s", flush=True)

    with ThreadPoolExecutor(CONCURRENCY) as pool:
        for _ in range(CONCURRENCY):
            pool.submit(worker, stop, lock, stats)

        deadline: float = time.monotonic() + DURATION_SECONDS
        while time.monotonic() < deadline and not stop.is_set():
            time.sleep(0.25)
        stop.set()

    ok: int = stats.pop("ok", 0)
    errors: int = sum(stats.values())
    print(f"[done] ok={ok} errors={errors}", flush=True)
    if errors:
        print("[errors] " + ", ".join(f"{name}:{count}" for name, count in sorted(stats.items())), flush=True)

if __name__ == "__main__":
    main()
