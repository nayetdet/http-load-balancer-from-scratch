from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Paths
    root_path: Path = Path(__file__).resolve().parents[2]
    resources_path: Path = root_path / "resources"
    templates_path: Path = resources_path / "templates"

settings = Settings()
