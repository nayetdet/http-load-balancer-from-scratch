from pydantic import BaseModel

class RouteSchema(BaseModel):
    route_id: str
    host: str
    port: int
