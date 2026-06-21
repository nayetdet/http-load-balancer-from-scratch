from http_load_balancer.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer.core.target_manager import TargetManager
from http_load_balancer.core.target_stats_manager import TargetStatsManager
from http_load_balancer.schemas.connection_schema import ConnectionSchema
from http_load_balancer.schemas.target_schema import TargetSchema

class LeastResponseTimeAlgorithm(BaseAlgorithm):
    @classmethod
    def next_target(cls, _: ConnectionSchema) -> TargetSchema:
        targets: list[TargetSchema] = TargetManager.targets()
        return min(
            enumerate(targets),
            key=lambda item: (TargetStatsManager.stats(item[1].key()).response_time, item[0])
        )[1]
