from http_load_balancer.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer.core.target_manager import TargetManager
from http_load_balancer.schemas.connection_schema import ConnectionSchema
from http_load_balancer.schemas.target_schema import TargetSchema

class WeightedRoundRobinAlgorithm(BaseAlgorithm):
    _index: int = 0
    _sequence_signature: tuple[str, ...] = ()
    _sequence: list[TargetSchema] = []

    @classmethod
    def next_target(cls, connection: ConnectionSchema) -> TargetSchema:
        targets: list[TargetSchema] = TargetManager.targets()
        signature: tuple[str, ...] = tuple(f"{target.key()}#{target.weight}" for target in targets)

        if signature != cls._sequence_signature:
            cls._sequence_signature = signature
            weighted_targets: list[TargetSchema] = []
            for target in targets:
                if target.weight > 0:
                    weighted_targets.extend([target] * target.weight)

            if not weighted_targets:
                raise ValueError("At least one target must have a positive weight.")

            cls._sequence = weighted_targets
            cls._index = 0

        sequence: list[TargetSchema] = cls._sequence
        index: int = cls._index % len(sequence)
        cls._index = (index + 1) % len(sequence)
        return sequence[index]
