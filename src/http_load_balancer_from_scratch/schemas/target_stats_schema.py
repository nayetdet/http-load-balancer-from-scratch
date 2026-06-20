from pydantic import BaseModel

class TargetStatsSchema(BaseModel):
    connections: int = 0
    response_time: float = 0
