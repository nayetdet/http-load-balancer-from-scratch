from abc import ABC, abstractmethod
from http_load_balancer.schemas.connection_schema import ConnectionSchema
from http_load_balancer.schemas.target_schema import TargetSchema

class BaseAlgorithm(ABC):
    @classmethod
    @abstractmethod
    def next_target(cls, connection: ConnectionSchema) -> TargetSchema:
        ...
