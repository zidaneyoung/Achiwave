import logging
from time import perf_counter

from fastapi import FastAPI, Request, status
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
from achiwave_backend.logging_config import configure_logging


class ServiceResponse(BaseModel):
    service: str
    environment: str
    status: str


def create_app(
    settings: Settings | None = None,
    *,
    database_check: HealthCheck | None = None,
    redis_check: HealthCheck | None = None,
    request_logger: logging.Logger | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    resolved_database_check = database_check or create_database_health_check(
        resolved_settings
    )
    resolved_redis_check = redis_check or create_redis_health_check(
        resolved_settings
    )
    resolved_request_logger = request_logger or logging.getLogger(
        "achiwave.http"
    )
    application = FastAPI(title="Achiwave API", version="0.1.0")
    application.state.settings = resolved_settings

    @application.middleware("http")
    async def log_request(request: Request, call_next):
        started_at = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            route = getattr(request.scope.get("route"), "path", "<unmatched>")
            resolved_request_logger.exception(
                "http_request_failed",
                extra={
                    "method": request.method,
                    "route": route,
                    "status_code": 500,
                    "duration_ms": round(
                        (perf_counter() - started_at) * 1000,
                        3,
                    ),
                },
            )
            raise

        route = getattr(request.scope.get("route"), "path", "<unmatched>")
        log_level = (
            logging.DEBUG
            if route in {"/health/live", "/health/ready"}
            else logging.INFO
        )
        resolved_request_logger.log(
            log_level,
            "http_request",
            extra={
                "method": request.method,
                "route": route,
                "status_code": response.status_code,
                "duration_ms": round(
                    (perf_counter() - started_at) * 1000,
                    3,
                ),
            },
        )
        return response

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


runtime_settings = get_settings()
configure_logging(runtime_settings)
app = create_app(runtime_settings)
