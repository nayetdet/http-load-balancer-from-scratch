from http_load_balancer_from_scratch.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer_from_scratch.schemas.connection_schema import ConnectionSchema
from http_load_balancer_from_scratch.schemas.target_schema import TargetSchema

class WeightedRoundRobinAlgorithm(BaseAlgorithm):
    _index: int = 0
    _sequence_signature: tuple[str, ...] = ()
    _sequence: list[TargetSchema] = []

    @classmethod
    def next_route(cls, connection: ConnectionSchema) -> TargetSchema:
        routes: list[TargetSchema] = cls.routes()
        signature: tuple[str, ...] = tuple(f"{route.key()}#{route.weight}" for route in routes)

        if signature != cls._sequence_signature:
            cls._sequence_signature = signature
            weighted_routes: list[TargetSchema] = []
            for route in routes:
                weighted_routes.extend([route] * max(1, route.weight))

            cls._sequence = weighted_routes or routes
            cls._index = 0

        sequence: list[TargetSchema] = cls._sequence or routes
        index: int = cls._index % len(sequence)
        cls._index = (index + 1) % len(sequence)
        return sequence[index]
