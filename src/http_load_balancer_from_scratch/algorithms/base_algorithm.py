from abc import ABC, abstractmethod
from http_load_balancer_from_scratch.schemas.connection_schema import ConnectionSchema
from http_load_balancer_from_scratch.schemas.target_schema import TargetSchema
from http_load_balancer_from_scratch.core.kubernetes_client import KubernetesClient

class BaseAlgorithm(ABC):
    @classmethod
    @abstractmethod
    def next_route(cls, connection: ConnectionSchema) -> TargetSchema:
        ...

    @staticmethod
    def routes() -> list[TargetSchema]:
        routes: list[TargetSchema] = KubernetesClient.targets()
        if not routes:
            raise RuntimeError("No available routes")
        return routes
