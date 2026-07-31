import logging
from time import perf_counter

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from achiwave_backend.api.auth import create_auth_router
from achiwave_backend.api.account import create_account_router
from achiwave_backend.api.dependencies import (
    create_authentication_dependencies,
    create_database_session_dependency,
)
from achiwave_backend.api.devices import create_devices_router, create_sessions_router
from achiwave_backend.api.errors import (
    ApiError,
    api_error_handler,
    validation_error_handler,
)
from achiwave_backend.api.preferences import create_preferences_router
from achiwave_backend.api.users import create_users_router
from fastapi.exceptions import RequestValidationError
from achiwave_backend.config import Settings, get_settings
from achiwave_backend.database import (
    SessionFactory,
    create_database_engine,
    create_session_factory,
)
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
    session_factory: SessionFactory | None = None,
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
    application.add_exception_handler(ApiError, api_error_handler)
    application.add_exception_handler(
        RequestValidationError,
        validation_error_handler,
    )

    resolved_session_factory = session_factory
    if resolved_session_factory is None and resolved_settings.database_url is not None:
        engine = create_database_engine(resolved_settings)
        application.state.database_engine = engine
        resolved_session_factory = create_session_factory(engine)
    database_session = create_database_session_dependency(
        resolved_session_factory
    )
    authentication = create_authentication_dependencies(
        resolved_settings,
        database_session,
    )
    application.include_router(create_auth_router(resolved_settings, database_session))
    application.include_router(create_users_router(authentication))
    application.include_router(create_devices_router(authentication))
    application.include_router(create_sessions_router(authentication))
    application.include_router(create_preferences_router(authentication))
    application.include_router(create_account_router(resolved_settings, authentication))

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
