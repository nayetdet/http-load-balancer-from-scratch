from __future__ import annotations

from typing import Self
from pydantic import BaseModel, Field, model_validator
from http_load_balancer.enums.algorithm_strategy import AlgorithmStrategy
from http_load_balancer.schemas.target_schema import TargetSchema

class TargetSettingsSchema(BaseModel):
    version: int = 1
    algorithm_strategy: AlgorithmStrategy = Field(default=AlgorithmStrategy.ROUND_ROBIN)
    targets: list[TargetSchema] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_targets(self) -> Self:
        if not self.targets:
            raise ValueError("At least one target must be configured.")
        return self
