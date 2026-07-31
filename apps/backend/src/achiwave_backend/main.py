from fastapi import FastAPI
from pydantic import BaseModel

from achiwave_backend.config import Settings, get_settings


class ServiceResponse(BaseModel):
    service: str
    environment: str
    status: str


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    application = FastAPI(title="Achiwave API", version="0.1.0")
    application.state.settings = resolved_settings

    @application.get("/", response_model=ServiceResponse)
    def service_metadata() -> ServiceResponse:
        return ServiceResponse(
            service="achiwave-backend",
            environment=resolved_settings.app_environment,
            status="ok",
        )

    return application


app = create_app()
