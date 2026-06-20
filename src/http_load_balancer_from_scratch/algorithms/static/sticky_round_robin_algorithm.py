from http_load_balancer_from_scratch.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer_from_scratch.schemas.connection_schema import ConnectionSchema
from http_load_balancer_from_scratch.schemas.target_schema import TargetSchema

class StickyRoundRobinAlgorithm(BaseAlgorithm):
    _index: int = 0
    _sticky_route_key_map: dict[str, str] = {}
    _sticky_signature: tuple[str, ...] = ()

    @classmethod
    def next_route(cls, connection: ConnectionSchema) -> TargetSchema:
        routes: list[TargetSchema] = cls.routes()
        signature: tuple[str, ...] = tuple(route.key() for route in routes)
        if signature != cls._sticky_signature:
            cls._sticky_signature = signature
            cls._sticky_route_key_map = {}

        client_key: str = connection.client_ip
        sticky_key: str | None = cls._sticky_route_key_map.get(client_key)
        if sticky_key is not None:
            for route in routes:
                if route.key() == sticky_key:
                    return route

        index: int = cls._index % len(routes)
        cls._index = (index + 1) % len(routes)
        selected: TargetSchema = routes[index]
        cls._sticky_route_key_map[client_key] = selected.key()
        return selected
