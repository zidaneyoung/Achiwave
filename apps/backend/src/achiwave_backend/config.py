from functools import lru_cache
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ApplicationEnvironment = Literal["development", "test", "production"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
ServiceName = Literal["backend", "worker", "scheduler"]
AccessTokenAlgorithm = Literal["HS256"]


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
    service_name: ServiceName = "backend"
    database_url: PostgresDsn | None = None
    redis_url: RedisDsn = RedisDsn("redis://localhost:6379/0")
    celery_broker_url: RedisDsn | None = None
    celery_result_backend: RedisDsn | None = None
    celery_task_always_eager: bool = False
    celery_beat_schedule_filename: Path = Path(".runtime/celerybeat-schedule")
    access_token_signing_key: SecretStr | None = None
    access_token_algorithm: AccessTokenAlgorithm = "HS256"
    access_token_issuer: str = "achiwave"
    access_token_audience: str = "achiwave-mobile"
    access_token_lifetime_seconds: int = Field(default=900, ge=60, le=3600)
    refresh_token_lifetime_seconds: int = Field(
        default=2_592_000,
        ge=86_400,
        le=7_776_000,
    )
    password_min_length: int = Field(default=12, ge=8, le=64)
    password_max_length: int = Field(default=128, ge=64, le=1024)
    database_connect_timeout_seconds: int = Field(default=3, ge=1, le=10)
    database_pool_size: int = Field(default=5, ge=1, le=20)
    database_max_overflow: int = Field(default=5, ge=0, le=20)
    database_pool_timeout_seconds: float = Field(default=3.0, gt=0, le=10)
    redis_connect_timeout_seconds: float = Field(default=1.0, gt=0, le=10)
    redis_socket_timeout_seconds: float = Field(default=1.0, gt=0, le=10)

    @model_validator(mode="after")
    def validate_security_configuration(self) -> Self:
        if self.password_max_length < self.password_min_length:
            raise ValueError(
                "ACHIWAVE_PASSWORD_MAX_LENGTH must not be less than "
                "ACHIWAVE_PASSWORD_MIN_LENGTH."
            )
        if self.app_environment == "production":
            signing_key = self.access_token_signing_key
            if signing_key is None or len(signing_key.get_secret_value()) < 32:
                raise ValueError(
                    "ACHIWAVE_ACCESS_TOKEN_SIGNING_KEY must contain at least "
                    "32 characters in production."
                )
        return self

    def require_database_url(self) -> str:
        if self.database_url is None:
            raise ValueError(
                "ACHIWAVE_DATABASE_URL is required for database operations."
            )
        return str(self.database_url)

    def require_redis_url(self) -> str:
        return str(self.redis_url)

    def require_access_token_signing_key(self) -> str:
        if self.access_token_signing_key is None:
            raise ValueError(
                "ACHIWAVE_ACCESS_TOKEN_SIGNING_KEY is required for "
                "authentication operations."
            )
        return self.access_token_signing_key.get_secret_value()

    def resolved_celery_broker_url(self) -> str:
        return str(self.celery_broker_url or self.redis_url)

    def resolved_celery_result_backend(self) -> str:
        return str(self.celery_result_backend or self.redis_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
