from __future__ import annotations

import yaml
from threading import Lock
from typing import TYPE_CHECKING
from loguru import logger
from http_load_balancer.algorithms.base_algorithm import BaseAlgorithm
from http_load_balancer.core.target_stats_manager import TargetStatsManager
from http_load_balancer.schemas.target_schema import TargetSchema

if TYPE_CHECKING:
    from http_load_balancer.enums.algorithm_strategy import AlgorithmStrategy
    from http_load_balancer.schemas.target_settings_schema import TargetSettingsSchema

class TargetManager:
    _lock = Lock()
    _version: int = 1
    _algorithm_strategy: AlgorithmStrategy | None = None
    _targets: set[TargetSchema] = set()

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
    def reload(cls, payload: TargetSettingsSchema | None = None, *_: object) -> None:
        try:
            from http_load_balancer.settings import settings
            from http_load_balancer.schemas.target_settings_schema import TargetSettingsSchema
            target_settings = TargetSettingsSchema.model_validate(yaml.safe_load(settings.settings_file_path.read_text(encoding="utf-8")) or {})
            if isinstance(payload, TargetSettingsSchema):
                target_settings = target_settings.model_copy(
                    update={
                        key: getattr(payload, key)
                        for key in ("version", "algorithm_strategy", "targets")
                        if key in payload.model_fields_set
                    }
                )

            with cls._lock:
                cls._version = target_settings.version
                cls._targets = {target.model_copy(deep=True) for target in target_settings.targets}
                cls._algorithm_strategy = target_settings.algorithm_strategy
                TargetStatsManager.reload()
        except Exception:
            logger.exception("Failed to reload target settings payload")
        else:
            logger.info("Target settings payload reloaded")
