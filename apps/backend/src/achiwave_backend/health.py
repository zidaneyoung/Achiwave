from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from achiwave_backend.config import Settings
from achiwave_backend.database import (
    DatabaseUnavailableError,
    create_database_engine,
    ping_database,
)
from achiwave_backend.redis_client import (
    RedisUnavailableError,
    create_redis_client,
    ping_redis,
)

DependencyState = Literal["ok", "unavailable"]
ReadinessState = Literal["ready", "not_ready"]
HealthCheck = Callable[[], None]


class LivenessResponse(BaseModel):
    status: Literal["ok"]


class DependencyChecks(BaseModel):
    postgresql: DependencyState
    redis: DependencyState


class ReadinessResponse(BaseModel):
    status: ReadinessState
    checks: DependencyChecks


def create_database_health_check(settings: Settings) -> HealthCheck:
    def check() -> None:
        try:
            engine = create_database_engine(settings)
        except (SQLAlchemyError, ValueError) as error:
            raise DatabaseUnavailableError(
                "PostgreSQL is unavailable."
            ) from error

        try:
            if not ping_database(engine):
                raise DatabaseUnavailableError("PostgreSQL is unavailable.")
        finally:
            engine.dispose()

    return check


def create_redis_health_check(settings: Settings) -> HealthCheck:
    def check() -> None:
        client = create_redis_client(settings)
        try:
            if not ping_redis(client):
                raise RedisUnavailableError("Redis is unavailable.")
        finally:
            client.close()

    return check


def evaluate_readiness(
    database_check: HealthCheck,
    redis_check: HealthCheck,
) -> ReadinessResponse:
    states: dict[str, DependencyState] = {}

    try:
        database_check()
        states["postgresql"] = "ok"
    except DatabaseUnavailableError:
        states["postgresql"] = "unavailable"

    try:
        redis_check()
        states["redis"] = "ok"
    except RedisUnavailableError:
        states["redis"] = "unavailable"

    checks = DependencyChecks(
        postgresql=states["postgresql"],
        redis=states["redis"],
    )
    return ReadinessResponse(
        status=(
            "ready"
            if checks.postgresql == "ok" and checks.redis == "ok"
            else "not_ready"
        ),
        checks=checks,
    )
