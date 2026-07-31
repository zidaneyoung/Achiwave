from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

ApplicationEnvironment = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class Settings(BaseSettings):
    """Validated, environment-backed backend settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="ACHIWAVE_",
        extra="ignore",
        validate_default=True,
    )

    app_environment: ApplicationEnvironment = "development"
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)
    log_level: LogLevel = "INFO"
    database_url: PostgresDsn | None = None
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    celery_broker_url: RedisDsn | None = None
    celery_result_backend: RedisDsn | None = None
    celery_task_always_eager: bool = False
    celery_beat_schedule_filename: Path = Path(".runtime/celerybeat-schedule")
    redis_connect_timeout_seconds: float = Field(default=1.0, gt=0, le=10)
    redis_socket_timeout_seconds: float = Field(default=1.0, gt=0, le=10)

    def require_database_url(self) -> str:
        if self.database_url is None:
            raise ValueError(
                "ACHIWAVE_DATABASE_URL is required for database operations."
            )
        return str(self.database_url)

    def require_redis_url(self) -> str:
        return str(self.redis_url)

    def resolved_celery_broker_url(self) -> str:
        return str(self.celery_broker_url or self.redis_url)

    def resolved_celery_result_backend(self) -> str:
        return str(self.celery_result_backend or self.redis_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
