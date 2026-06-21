from http_load_balancer.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer.core.target_manager import TargetManager
from http_load_balancer.schemas.connection_schema import ConnectionSchema
from http_load_balancer.schemas.target_schema import TargetSchema

class StickyRoundRobinAlgorithm(BaseAlgorithm):
    _index: int = 0
    _sticky_target_key_map: dict[str, str] = {}
    _sticky_signature: tuple[str, ...] = ()

    @classmethod
    def next_target(cls, connection: ConnectionSchema) -> TargetSchema:
        targets: list[TargetSchema] = list(TargetManager.targets())
        signature: tuple[str, ...] = tuple(sorted(target.key() for target in targets))
        if signature != cls._sticky_signature:
            cls._sticky_signature = signature
            valid_target_keys: set[str] = set(signature)
            cls._sticky_target_key_map = {
                client_key: target_key
                for client_key, target_key in cls._sticky_target_key_map.items()
                if target_key in valid_target_keys
            }

        client_key: str = connection.client_ip
        sticky_key: str | None = cls._sticky_target_key_map.get(client_key)
        if sticky_key is not None:
            for target in targets:
                if target.key() == sticky_key:
                    return target

        index: int = cls._index % len(targets)
        cls._index = (index + 1) % len(targets)
        selected: TargetSchema = targets[index]
        cls._sticky_target_key_map[client_key] = selected.key()
        return selected
