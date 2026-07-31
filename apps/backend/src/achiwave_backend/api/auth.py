from collections.abc import Iterator

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.auth.passwords import PasswordManager, PasswordPolicyError
from achiwave_backend.auth.tokens import TokenIssuer
from achiwave_backend.config import Settings
from achiwave_backend.database import SessionFactory
from achiwave_backend.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    RegistrationRequest,
    RegistrationResponse,
    SafeUserResponse,
)
from achiwave_backend.services.login import (
    AccountUnavailableError,
    DeviceContextMismatchError,
    InvalidCredentialsError,
    LoginService,
)
from achiwave_backend.services.registration import (
    EmailAlreadyRegisteredError,
    RegistrationService,
)
from achiwave_backend.services.refresh import (
    InvalidRefreshTokenError,
    RefreshAccountUnavailableError,
    RefreshDeviceRevokedError,
    RefreshService,
    RefreshTokenReuseError,
    SessionExpiredError,
    SessionRevokedError,
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

    @router.post(
        "/login",
        response_model=LoginResponse,
        responses={
            status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        },
    )
    def login(
        request: LoginRequest,
        session: Session = Depends(database_session),
    ) -> LoginResponse:
        try:
            login_service = LoginService(password_manager, TokenIssuer(settings))
            result = login_service.login(session, request)
        except InvalidCredentialsError as error:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="invalid_credentials",
                message="The supplied credentials are invalid.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        except AccountUnavailableError as error:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="account_deactivated",
                message="This account is not available.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        except DeviceContextMismatchError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="invalid_device_context",
                message="The supplied device context is invalid.",
            ) from error

        return LoginResponse(
            user=SafeUserResponse(
                id=result.user.id,
                email=result.user.display_email,
                account_state="active",
                record_version=result.user.record_version,
            ),
            timezone_name=result.preference.timezone_name,
            device_id=result.device.id,
            session_id=result.session.id,
            session_expires_at=result.session.expires_at,
            access_token=result.credentials.access_token,
            access_token_expires_at=result.credentials.access_expires_at,
            refresh_token=result.credentials.refresh_token,
        )

    @router.post(
        "/refresh",
        response_model=RefreshResponse,
        responses={status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse}},
    )
    def refresh(
        request: RefreshRequest,
        session: Session = Depends(database_session),
    ) -> RefreshResponse:
        try:
            result = RefreshService(TokenIssuer(settings)).refresh(session, request)
        except InvalidRefreshTokenError as error:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="invalid_refresh_token",
                message="The refresh credential is invalid.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        except SessionExpiredError as error:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="session_expired",
                message="The session has expired.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        except SessionRevokedError as error:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="session_revoked",
                message="The session is no longer active.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        except RefreshTokenReuseError as error:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="refresh_token_reuse_detected",
                message="The session is no longer active.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        except RefreshDeviceRevokedError as error:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="device_revoked",
                message="The registered device is no longer active.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error
        except RefreshAccountUnavailableError as error:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="account_deactivated",
                message="This account is not available.",
                headers={"WWW-Authenticate": "Bearer"},
            ) from error

        return RefreshResponse(
            session_id=result.session.id,
            session_expires_at=result.session.expires_at,
            access_token=result.credentials.access_token,
            access_token_expires_at=result.credentials.access_expires_at,
            refresh_token=result.credentials.refresh_token,
        )

    return router
