from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from achiwave_backend.auth.passwords import PasswordManager
from achiwave_backend.auth.tokens import IssuedCredentials, TokenIssuer
from achiwave_backend.models import (
    DeviceSession,
    RegisteredDevice,
    User,
    UserPreference,
)
from achiwave_backend.schemas.auth import LoginRequest
from achiwave_backend.services.registration import canonicalize_email


class InvalidCredentialsError(ValueError):
    """Email/password pair could not establish identity."""


class AccountUnavailableError(ValueError):
    """Verified account is not active."""


class DeviceContextMismatchError(ValueError):
    """Known installation conflicts with supplied public context."""


@dataclass(frozen=True, slots=True)
class LoginResult:
    user: User
    preference: UserPreference
    device: RegisteredDevice
    session: DeviceSession
    credentials: IssuedCredentials


class LoginService:
    def __init__(
        self,
        password_manager: PasswordManager,
        token_issuer: TokenIssuer,
    ) -> None:
        self._password_manager = password_manager
        self._token_issuer = token_issuer

    def login(
        self,
        database_session: Session,
        request: LoginRequest,
    ) -> LoginResult:
        now = datetime.now(UTC)
        canonical_email = canonicalize_email(str(request.email))

        with database_session.begin():
            user = database_session.scalar(
                select(User).where(User.canonical_email == canonical_email)
            )
            valid, replacement_hash = self._password_manager.verify(
                request.password,
                user.password_hash if user is not None else None,
            )
            if user is None or not valid:
                raise InvalidCredentialsError
            if user.account_state != "active":
                raise AccountUnavailableError
            if replacement_hash is not None:
                user.password_hash = replacement_hash
                user.record_version += 1
                user.updated_at = now

            preference = database_session.get(UserPreference, user.id)
            if preference is None:
                raise RuntimeError("Active user preference record is missing.")

            device = database_session.scalar(
                select(RegisteredDevice).where(
                    RegisteredDevice.user_id == user.id,
                    RegisteredDevice.installation_id
                    == str(request.installation.installation_id),
                    RegisteredDevice.app_environment
                    == request.installation.app_environment,
                    RegisteredDevice.device_state == "active",
                )
            )
            if device is not None and device.platform != request.installation.platform:
                raise DeviceContextMismatchError
            if device is None:
                device = RegisteredDevice(
                    user_id=user.id,
                    platform=request.installation.platform,
                    installation_id=str(request.installation.installation_id),
                    app_environment=request.installation.app_environment,
                    app_version=request.installation.app_version,
                    build_version=request.installation.build_version,
                    last_seen_at=now,
                )
                database_session.add(device)
                database_session.flush()
            else:
                device.app_version = request.installation.app_version
                device.build_version = request.installation.build_version
                device.last_seen_at = now
                device.updated_at = now
                device.record_version += 1

            session = DeviceSession(
                id=uuid4(),
                user_id=user.id,
                device_id=device.id,
                expires_at=now,
            )
            credentials = self._token_issuer.issue(
                user_id=user.id,
                session_id=session.id,
                now=now,
            )
            session.expires_at = credentials.refresh_expires_at
            session.credential_digest = credentials.refresh_token_digest
            database_session.add(session)
            database_session.flush()

        return LoginResult(
            user=user,
            preference=preference,
            device=device,
            session=session,
            credentials=credentials,
        )
