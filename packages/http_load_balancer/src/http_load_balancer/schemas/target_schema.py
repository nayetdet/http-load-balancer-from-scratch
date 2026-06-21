from pydantic import BaseModel, Field

class TargetSchema(BaseModel):
    ip: str
    port: int
    weight: int = Field(default=1, ge=1)

    def __hash__(self) -> int:
        return hash((self.ip, self.port))

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TargetSchema) and (self.ip, self.port) == (other.ip, other.port)

    def key(self) -> str:
        return f"{self.ip}:{self.port}"
