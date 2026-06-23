from __future__ import annotations

import requests
from loguru import logger
from http_target_discovery.providers.base_provider import BaseProvider
from http_target_discovery.settings import settings

class SynchronizationManager:
    _session: requests.Session | None = None
    _last_seen: tuple[tuple[str, int, int], ...] | None = None
    _last_sent: tuple[tuple[str, int, int], ...] | None = None

    @classmethod
    def synchronize(cls, provider: type[BaseProvider]) -> None:
        session = cls._session
        if session is None:
            raise RuntimeError("SynchronizationManager._session must be set before synchronize()")
        
        try:
            discovered = list(provider.targets())
        except Exception:
            logger.exception("Failed to discover targets")
            return

        current_targets: list[dict] = []

        try:
            response = session.get(
                settings.lb_settings_url,
                timeout=settings.request_timeout_seconds,
            )
            response.raise_for_status()

            current_targets = response.json().get("targets", [])
        except (requests.RequestException, OSError, ValueError):
            logger.exception("Failed to fetch current load balancer settings")

        current_by_endpoint = {
            (target["ip"], target["port"]): target["weight"]
            for target in current_targets
        }

        matched_count = 0
        synchronized_targets = []

        for target in discovered:
            weight = current_by_endpoint.get((target.ip, target.port))

            if weight is not None:
                matched_count += 1
            else:
                weight = target.weight

            synchronized_targets.append((target.ip, target.port, weight))

        if matched_count == 0 and current_targets:
            synchronized_targets = []

            for index, target in enumerate(discovered):
                weight = target.weight

                if index < len(current_targets):
                    weight = current_targets[index]["weight"]

                synchronized_targets.append((target.ip, target.port, weight))

        targets = tuple(sorted(synchronized_targets))

        if cls._last_seen != targets:
            logger.info("Target set changed: {}", targets)

        if cls._last_sent != targets:
            try:
                response = session.post(
                    url=settings.lb_reload_url,
                    json={
                        "targets": [
                            {"ip": ip, "port": port, "weight": weight}
                            for ip, port, weight in targets
                        ]
                    },
                    timeout=settings.request_timeout_seconds
                )

                response.raise_for_status()
            except (requests.RequestException, OSError):
                logger.exception("Failed to reload load balancer")
            else:
                cls._last_sent = targets
                logger.info("Reloaded load balancer with {} targets", len(targets))

        cls._last_seen = targets

    @classmethod
    def close(cls) -> None:
        session = cls._session
        if session is not None:
            session.close()
            cls._session = None
