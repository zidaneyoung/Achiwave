from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from achiwave_backend.api.errors import ApiError
from achiwave_backend.auth.tokens import (
    AccessTokenExpiredError,
    InvalidAccessTokenError,
    TokenVerifier,
)
from achiwave_backend.config import Settings
from achiwave_backend.database import SessionFactory
from achiwave_backend.models import DeviceSession, RegisteredDevice, User

DatabaseSessionDependency = Callable[[], Iterator[Session]]


@dataclass(frozen=True, slots=True)
class AuthenticationContext:
    user: User
    session: DeviceSession
    device: RegisteredDevice


@dataclass(frozen=True, slots=True)
class AuthenticationDependencies:
    database_session: DatabaseSessionDependency
    current_context: Callable[..., AuthenticationContext]
    current_user: Callable[..., User]
    current_session: Callable[..., DeviceSession]
    current_device: Callable[..., RegisteredDevice]


def _unauthenticated(code: str, message: str) -> ApiError:
    return ApiError(
        status_code=status.HTTP_401_UNAUTHORIZED,
        code=code,
        message=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


def create_database_session_dependency(
    session_factory: SessionFactory | None,
) -> DatabaseSessionDependency:
    def database_session() -> Iterator[Session]:
        if session_factory is None:
            raise ApiError(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                code="dependency_unavailable",
                message="The requested service is temporarily unavailable.",
            )
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    return database_session


def create_authentication_dependencies(
    settings: Settings,
    database_session: DatabaseSessionDependency,
) -> AuthenticationDependencies:
    bearer = HTTPBearer(auto_error=False)

    def current_context(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
        session: Session = Depends(database_session),
    ) -> AuthenticationContext:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise _unauthenticated(
                "invalid_access_token",
                "Authentication is required.",
            )
        try:
            claims = TokenVerifier(settings).verify(credentials.credentials)
        except AccessTokenExpiredError as error:
            raise _unauthenticated(
                "session_expired",
                "The session has expired.",
            ) from error
        except InvalidAccessTokenError as error:
            raise _unauthenticated(
                "invalid_access_token",
                "The access token is invalid.",
            ) from error
        except ValueError as error:
            raise ApiError(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                code="dependency_unavailable",
                message="Authentication is temporarily unavailable.",
            ) from error

        device_session = session.scalar(
            select(DeviceSession).where(
                DeviceSession.id == claims.session_id,
                DeviceSession.user_id == claims.user_id,
            )
        )
        if device_session is None:
            raise _unauthenticated(
                "invalid_access_token",
                "The access token is invalid.",
            )
        if (
            device_session.session_state == "expired"
            or device_session.expires_at <= datetime.now(UTC)
        ):
            raise _unauthenticated("session_expired", "The session has expired.")
        if device_session.session_state != "active":
            raise _unauthenticated(
                "session_revoked",
                "The session is no longer active.",
            )

        user = session.get(User, claims.user_id)
        if user is None:
            raise _unauthenticated(
                "invalid_access_token",
                "The access token is invalid.",
            )
        if user.account_state != "active":
            raise _unauthenticated(
                "account_deactivated",
                "This account is not available.",
            )

        device = session.scalar(
            select(RegisteredDevice).where(
                RegisteredDevice.id == device_session.device_id,
                RegisteredDevice.user_id == user.id,
            )
        )
        if device is None:
            raise _unauthenticated(
                "invalid_access_token",
                "The access token is invalid.",
            )
        if device.device_state != "active":
            raise _unauthenticated(
                "device_revoked",
                "The registered device is no longer active.",
            )
        return AuthenticationContext(
            user=user,
            session=device_session,
            device=device,
        )

    def current_user(
        context: AuthenticationContext = Depends(current_context),
    ) -> User:
        return context.user

    def current_session(
        context: AuthenticationContext = Depends(current_context),
    ) -> DeviceSession:
        return context.session

    def current_device(
        context: AuthenticationContext = Depends(current_context),
    ) -> RegisteredDevice:
        return context.device

    return AuthenticationDependencies(
        database_session=database_session,
        current_context=current_context,
        current_user=current_user,
        current_session=current_session,
        current_device=current_device,
    )
