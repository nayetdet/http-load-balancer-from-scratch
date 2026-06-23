from enum import Enum
from http_target_discovery.providers.base_provider import BaseProvider
from http_target_discovery.providers.docker_provider import DockerProvider
from http_target_discovery.providers.kubernetes_provider import KubernetesProvider

class ProviderStrategy(str, Enum):
    DOCKER = ("docker", DockerProvider)
    KUBERNETES = ("kubernetes", KubernetesProvider)

    def __new__(cls, name: str, provider: type[BaseProvider]):
        obj = str.__new__(cls, name)
        obj._value_ = name
        obj.provider = provider
        return obj

    def __init__(self, name: str, provider: type[BaseProvider]):
        self.label = name
