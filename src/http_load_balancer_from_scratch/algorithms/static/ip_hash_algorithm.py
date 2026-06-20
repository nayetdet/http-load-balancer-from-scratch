import hashlib
from http_load_balancer_from_scratch.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer_from_scratch.schemas.connection_schema import ConnectionSchema
from http_load_balancer_from_scratch.schemas.target_schema import TargetSchema

class IPHashAlgorithm(BaseAlgorithm):
    @classmethod
    def next_route(cls, connection: ConnectionSchema) -> TargetSchema:
        routes: list[TargetSchema] = cls.routes()
        digest: bytes = hashlib.sha256(connection.client_ip.encode("utf-8")).digest()
        index: int = int.from_bytes(digest[:8], "big") % len(routes)
        return routes[index]
