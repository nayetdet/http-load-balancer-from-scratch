from pydantic import BaseModel, Field
from http_load_balancer_from_scratch.schemas.target_stats_schema import TargetStatsSchema

class TargetSchema(BaseModel):
    target_id: str
    ip: str
    port: int
    weight: int = 1
    stats: TargetStatsSchema = Field(default_factory=TargetStatsSchema)

    def key(self) -> str:
        return self.target_id
