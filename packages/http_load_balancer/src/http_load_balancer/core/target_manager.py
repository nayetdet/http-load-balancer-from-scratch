from __future__ import annotations

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
    from http_load_balancer.schemas.target_settings_schema import TargetSettingsSchema

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
    def reload(cls, payload: TargetSettingsSchema | None = None) -> None:
        try:
            from http_load_balancer.schemas.target_settings_schema import TargetSettingsSchema
            if payload is None:
                target_settings: TargetSettingsSchema = TargetSettingsSchema.model_validate(yaml.safe_load(settings.settings_file_path.read_text(encoding="utf-8")) or {})
            else:
                target_settings = payload

            targets: set[TargetSchema] = {target.model_copy(deep=True) for target in target_settings.targets}
            algorithm_strategy = target_settings.algorithm_strategy

            with cls._lock:
                cls._targets = {target.model_copy(deep=True) for target in targets}
                cls._algorithm_strategy = algorithm_strategy
                TargetStatsManager.reload()
        except Exception:
            logger.exception("Failed to reload target settings payload")
        else:
            logger.info("Target settings payload reloaded")
