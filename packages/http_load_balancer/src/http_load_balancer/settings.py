import yaml
from pathlib import Path
from typing import Self
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LB_",
        extra="ignore"
    )

    # Servers
    host: str = "0.0.0.0"
    proxy_port: int = 8080
    internal_port: int = 9090
    buffer_size: int = 4096
    backlog: int = 128

    # Paths
    root_path: Path = Path(__file__).resolve().parents[2]
    settings_path: Path = root_path / "settings"
    settings_file_path: Path = settings_path / "targets.yaml"

    @model_validator(mode="after")
    def setup_paths(self) -> Self:
        self.settings_path.mkdir(parents=True, exist_ok=True)
        if not self.settings_file_path.exists():
            from http_load_balancer.schemas.target_settings_schema import TargetSettingsSchema
            self.settings_file_path.write_text(yaml.safe_dump(TargetSettingsSchema().model_dump(mode="json"), sort_keys=False), encoding="utf-8")
        return self

settings = Settings()
