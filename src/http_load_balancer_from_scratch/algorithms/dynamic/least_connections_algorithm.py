from http_load_balancer_from_scratch.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer_from_scratch.schemas.connection_schema import ConnectionSchema
from http_load_balancer_from_scratch.schemas.target_schema import TargetSchema

class LeastConnectionsAlgorithm(BaseAlgorithm):
    @classmethod
    def next_route(cls, _: ConnectionSchema) -> TargetSchema:
        routes: list[TargetSchema] = cls.routes()
        return min(
            enumerate(routes),
            key=lambda item: (item[1].stats.connections, item[0])
        )[1]
