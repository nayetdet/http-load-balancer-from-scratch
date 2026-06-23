from __future__ import annotations

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timezone
from loguru import logger
from http_target_discovery.core.syncronization_manager import SynchronizationManager
from http_target_discovery.providers.base_provider import BaseProvider
from http_target_discovery.settings import settings

def main() -> None:
    logger.info(
        "Watching {} targets every {}s and reloading {}",
        settings.provider_strategy.label,
        settings.poll_interval_seconds,
        settings.lb_reload_url
    )

    provider: type[BaseProvider] = settings.provider_strategy.provider
    scheduler = BlockingScheduler(timezone=timezone.utc)
    try:
        scheduler.add_job(
            SynchronizationManager.synchronize,
            args=[provider],
            trigger=IntervalTrigger(seconds=settings.poll_interval_seconds),
            next_run_time=datetime.now(timezone.utc),
            coalesce=True,
            max_instances=1
        )

        scheduler.start()
    finally:
        SynchronizationManager.close()

if __name__ == "__main__":
    main()
