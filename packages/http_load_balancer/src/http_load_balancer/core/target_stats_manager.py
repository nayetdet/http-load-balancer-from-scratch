from collections import defaultdict
from threading import Lock
from http_load_balancer.schemas.target_stats_schema import TargetStatsSchema

class TargetStatsManager:
    _lock = Lock()
    _stats: defaultdict[str, TargetStatsSchema] = defaultdict(TargetStatsSchema)

    @classmethod
    def stats(cls, target_key: str) -> TargetStatsSchema:
        with cls._lock:
            return cls._stats.get(target_key, TargetStatsSchema()).model_copy(deep=True)

    @classmethod
    def increment_connections(cls, target_key: str) -> None:
        with cls._lock:
            cls._stats[target_key].connections += 1

    @classmethod
    def decrement_connections(cls, target_key: str) -> None:
        with cls._lock:
            stats = cls._stats[target_key]
            stats.connections = max(0, stats.connections - 1)

    @classmethod
    def update_response_time(cls, target_key: str, response_time: float) -> None:
        with cls._lock:
            cls._stats[target_key].response_time = response_time
