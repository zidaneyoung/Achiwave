from collections.abc import Iterator

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.auth.passwords import PasswordManager, PasswordPolicyError
from achiwave_backend.auth.tokens import TokenIssuer
from achiwave_backend.config import Settings
from achiwave_backend.database import SessionFactory
from achiwave_backend.schemas.auth import (
    RegistrationRequest,
    RegistrationResponse,
    SafeUserResponse,
)
from achiwave_backend.services.registration import (
    EmailAlreadyRegisteredError,
    RegistrationService,
)


def create_auth_router(
    settings: Settings,
    session_factory: SessionFactory | None,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])
    password_manager = PasswordManager(settings)

    def database_session() -> Iterator[Session]:
        if session_factory is None:
            raise ApiError(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                code="dependency_unavailable",
                message="Authentication is temporarily unavailable.",
            )
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    @router.post(
        "/register",
        response_model=RegistrationResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_409_CONFLICT: {"model": ErrorResponse},
            status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        },
    )
    def register(
        request: RegistrationRequest,
        session: Session = Depends(database_session),
    ) -> RegistrationResponse:
        try:
            registration_service = RegistrationService(
                password_manager,
                TokenIssuer(settings),
            )
            result = registration_service.register(session, request)
        except PasswordPolicyError as error:
            raise ApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="validation_error",
                message=str(error),
            ) from error
        except EmailAlreadyRegisteredError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="email_already_registered",
                message="An account cannot be registered with those credentials.",
            ) from error
        except ValueError as error:
            if not str(error).startswith("ACHIWAVE_ACCESS_TOKEN_SIGNING_KEY"):
                raise
            raise ApiError(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                code="dependency_unavailable",
                message="Authentication is temporarily unavailable.",
            ) from error

        return RegistrationResponse(
            user=SafeUserResponse(
                id=result.user.id,
                email=result.user.display_email,
                account_state="active",
                record_version=result.user.record_version,
            ),
            timezone_name=result.preference.timezone_name,
            timezone_was_defaulted=result.timezone_was_defaulted,
            device_id=result.device.id,
            session_id=result.session.id,
            session_expires_at=result.session.expires_at,
            access_token=result.credentials.access_token,
            access_token_expires_at=result.credentials.access_expires_at,
            refresh_token=result.credentials.refresh_token,
        )

    return router
