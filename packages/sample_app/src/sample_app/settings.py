from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Paths
    ROOT_PATH: Path = Path(__file__).resolve().parents[2]
    RESOURCES_PATH: Path = ROOT_PATH / "resources"
    TEMPLATES_PATH: Path = RESOURCES_PATH / "templates"

settings = Settings()
