from abc import ABC, abstractmethod
from http_target_discovery.schemas.target_schema import TargetSchema

class BaseProvider(ABC):
    @classmethod
    @abstractmethod
    def targets(cls) -> set[TargetSchema]:
        ...
