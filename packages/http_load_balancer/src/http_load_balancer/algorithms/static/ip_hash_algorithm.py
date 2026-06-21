import hashlib
from http_load_balancer.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer.core.target_manager import TargetManager
from http_load_balancer.schemas.connection_schema import ConnectionSchema
from http_load_balancer.schemas.target_schema import TargetSchema

class IPHashAlgorithm(BaseAlgorithm):
    @classmethod
    def next_target(cls, connection: ConnectionSchema) -> TargetSchema:
        targets: list[TargetSchema] = list(TargetManager.targets())
        digest: bytes = hashlib.sha256(connection.client_ip.encode("utf-8")).digest()
        index: int = int.from_bytes(digest[:8], "big") % len(targets)
        return targets[index]
