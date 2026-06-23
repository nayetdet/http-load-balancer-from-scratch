from pydantic_settings import BaseSettings, SettingsConfigDict
from http_target_discovery.enums.provider_strategy import ProviderStrategy
from http_target_discovery.enums.network_strategy import NetworkStrategy

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="DISCOVERY_",
        extra="ignore"
    )

    # Discovery
    provider_strategy: ProviderStrategy = ProviderStrategy.DOCKER
    network_strategy: NetworkStrategy = NetworkStrategy.PUBLISHED
    poll_interval_seconds: float = 5
    request_timeout_seconds: float = 5

    # Load Balancer
    lb_targets_url: str

    # Docker
    docker_target_label: str = "http-load-balancer.target"

    # Kubernetes
    kubernetes_deployment_name: str
    kubernetes_deployment_app_name: str
    kubernetes_namespace: str = "default"

settings = Settings()
