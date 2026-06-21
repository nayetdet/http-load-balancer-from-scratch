from http_load_balancer.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer.core.target_manager import TargetManager
from http_load_balancer.schemas.connection_schema import ConnectionSchema
from http_load_balancer.schemas.target_schema import TargetSchema

class RoundRobinAlgorithm(BaseAlgorithm):
    _index: int = 0

    @classmethod
    def next_target(cls, connection: ConnectionSchema) -> TargetSchema:
        targets: list[TargetSchema] = list(TargetManager.targets())
        index: int = cls._index % len(targets)
        cls._index = (index + 1) % len(targets)
        return targets[index]
