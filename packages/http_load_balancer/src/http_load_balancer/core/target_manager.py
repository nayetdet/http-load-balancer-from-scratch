import yaml
from threading import Lock
from typing import TYPE_CHECKING
from loguru import logger
from http_load_balancer.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer.core.target_stats_manager import TargetStatsManager
from http_load_balancer.schemas.target_schema import TargetSchema
from http_load_balancer.settings import settings

if TYPE_CHECKING:
    from http_load_balancer.enums.algorithm_strategy import AlgorithmStrategy

class TargetManager:
    _lock = Lock()
    _targets: set[TargetSchema] = set()
    _algorithm_strategy: AlgorithmStrategy | None = None

    @classmethod
    def targets(cls) -> set[TargetSchema]:
        with cls._lock:
            return {target.model_copy(deep=True) for target in cls._targets}

    @classmethod
    def algorithm(cls) -> type[BaseAlgorithm]:
        with cls._lock:
            if cls._algorithm_strategy is None:
                raise RuntimeError("TargetManager.reload() must run before algorithm lookup")
            return cls._algorithm_strategy.algorithm

    @classmethod
    def reload(cls, *_: object) -> None:
        try:
            from http_load_balancer.schemas.target_settings_schema import TargetSettingsSchema
            target_settings: TargetSettingsSchema = TargetSettingsSchema.model_validate(yaml.safe_load(settings.settings_file_path.read_text(encoding="utf-8")) or {})
            targets: set[TargetSchema] = {target.model_copy(deep=True) for target in target_settings.targets}
            with cls._lock:
                cls._targets = {target.model_copy(deep=True) for target in targets}
                cls._algorithm_strategy = target_settings.algorithm_strategy
                TargetStatsManager.reload()
        except Exception:
            logger.exception("Failed to reload target settings from {}", settings.settings_file_path)
        else:
            logger.info("Target settings reloaded from {}", settings.settings_file_path)
