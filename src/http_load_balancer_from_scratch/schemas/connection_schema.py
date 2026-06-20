from pydantic import BaseModel

class ConnectionSchema(BaseModel):
    client_ip: str
    client_port: int | None = None
