from pydantic_settings import BaseSettings, SettingsConfigDict
from http_target_discovery.enums.discovery_provider_strategy import DiscoveryProviderStrategy
from http_target_discovery.enums.discovery_target_network_strategy import DiscoveryTargetNetworkStrategy

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DISCOVERY_",
        extra="ignore"
    )

    # Discovery
    provider_strategy: DiscoveryProviderStrategy = DiscoveryProviderStrategy.DOCKER
    target_network_strategy: DiscoveryTargetNetworkStrategy = DiscoveryTargetNetworkStrategy.PUBLISHED
    poll_interval_seconds: float = 5
    request_timeout_seconds: float = 5

    # Load Balancer
    lb_reload_url: str

    # Docker
    docker_target_label: str = "http-load-balancer.target"

    # Kubernetes
    kubernetes_deployment_name: str
    kubernetes_deployment_app_name: str
    kubernetes_namespace: str = "default"

settings = Settings()
