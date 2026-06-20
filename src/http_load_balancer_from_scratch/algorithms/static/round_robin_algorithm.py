from http_load_balancer_from_scratch.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer_from_scratch.schemas.connection_schema import ConnectionSchema
from http_load_balancer_from_scratch.schemas.target_schema import TargetSchema

class RoundRobinAlgorithm(BaseAlgorithm):
    _index: int = 0

    @classmethod
    def next_route(cls, connection: ConnectionSchema) -> TargetSchema:
        routes: list[TargetSchema] = cls.routes()
        index: int = cls._index % len(routes)
        cls._index = (index + 1) % len(routes)
        return routes[index]
