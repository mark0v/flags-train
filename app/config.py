from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: str = Field(alias="BOT_TOKEN")
    app_env: str = Field(default="dev", alias="APP_ENV")
    database_url: str = Field(alias="DATABASE_URL")
    countries_data_path: Path = Field(alias="COUNTRIES_DATA_PATH")
    flags_dir: Path = Field(alias="FLAGS_DIR")
    quiz_autonext_seconds: float = Field(default=1.2, alias="QUIZ_AUTONEXT_SECONDS")

    @property
    def base_dir(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def resolve_path(self, path: Path) -> Path:
        if path.is_absolute():
            return path
        return self.base_dir / path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
