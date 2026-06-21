from pydantic import BaseModel, Field

class TargetSchema(BaseModel):
    ip: str
    port: int
    weight: int = Field(default=1, ge=1)

    def key(self) -> str:
        return f"{self.ip}:{self.port}"
