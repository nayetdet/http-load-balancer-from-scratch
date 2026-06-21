from pathlib import Path
from typing import Self
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="LB_",
        extra="ignore",
    )

    # Load Balancer
    host: str = "127.0.0.1"
    port: int = 8080
    buffer_size: int = 4096
    backlog: int = 128

    # Paths
    root_path: Path = Path(__file__).resolve().parents[2]
    settings_path: Path = root_path / "settings"
    settings_file_path: Path = settings_path / "targets.yaml"

    @model_validator(mode="after")
    def validate_paths(self) -> Self:
        for path in (self.settings_path,):
            path.mkdir(parents=True, exist_ok=True)

        for required_path in ("settings_file_path",):
            path: Path = getattr(self, required_path)
            if not path.exists():
                raise ValueError(f"{required_path} does not exist: '{path}'")

        return self

settings = Settings()
