from __future__ import annotations

from pydantic import BaseModel, Field
from http_target_discovery.enums.algorithm_strategy import AlgorithmStrategy
from http_target_discovery.schemas.target_schema import TargetSchema

class TargetSettingsSchema(BaseModel):
    version: int = 1
    algorithm_strategy: AlgorithmStrategy = Field(default=AlgorithmStrategy.ROUND_ROBIN)
    targets: list[TargetSchema] = Field(default_factory=list)
