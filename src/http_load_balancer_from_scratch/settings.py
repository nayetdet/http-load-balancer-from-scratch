from pathlib import Path
from typing import Self
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Paths
    ROOT_PATH: Path = Path(__file__).resolve().parents[2]
    CONFIG_PATH: Path = ROOT_PATH / "config"
    CONFIG_FILE_PATH: Path = CONFIG_PATH / "proxy.csv"

settings = Settings()
