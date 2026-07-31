from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from achiwave_backend.config import Settings, get_settings
from achiwave_backend.health import (
    HealthCheck,
    LivenessResponse,
    ReadinessResponse,
    create_database_health_check,
    create_redis_health_check,
    evaluate_readiness,
)


class ServiceResponse(BaseModel):
    service: str
    environment: str
    status: str


def create_app(
    settings: Settings | None = None,
    *,
    database_check: HealthCheck | None = None,
    redis_check: HealthCheck | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_database_check = database_check or create_database_health_check(
        resolved_settings
    )
    resolved_redis_check = redis_check or create_redis_health_check(
        resolved_settings
    )
    application = FastAPI(title="Achiwave API", version="0.1.0")
    application.state.settings = resolved_settings

    @application.get("/", response_model=ServiceResponse)
    def service_metadata() -> ServiceResponse:
        return ServiceResponse(
            service="achiwave-backend",
            environment=resolved_settings.app_environment,
            status="ok",
        )

    @application.get("/health/live", response_model=LivenessResponse)
    def liveness() -> LivenessResponse:
        return LivenessResponse(status="ok")

    @application.get(
        "/health/ready",
        response_model=ReadinessResponse,
        responses={
            status.HTTP_503_SERVICE_UNAVAILABLE: {
                "model": ReadinessResponse,
            }
        },
    )
    def readiness() -> ReadinessResponse | JSONResponse:
        response = evaluate_readiness(
            resolved_database_check,
            resolved_redis_check,
        )
        if response.status == "not_ready":
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content=response.model_dump(),
            )
        return response

    return application


app = create_app()
