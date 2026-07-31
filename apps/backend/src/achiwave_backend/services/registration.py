import re
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from achiwave_backend.auth.passwords import PasswordManager
from achiwave_backend.auth.tokens import IssuedCredentials, TokenIssuer
from achiwave_backend.models import (
    DeviceSession,
    RegisteredDevice,
    User,
    UserPreference,
)
from achiwave_backend.schemas.auth import RegistrationRequest

IANA_TIMEZONE = re.compile(
    r"^[A-Za-z]+(?:[_+-][A-Za-z0-9]+)*/[A-Za-z0-9_+-]+"
    r"(?:/[A-Za-z0-9_+-]+)*$"
)


class EmailAlreadyRegisteredError(ValueError):
    """Canonical email is already owned by an account."""


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    user: User
    preference: UserPreference
    device: RegisteredDevice
    session: DeviceSession
    credentials: IssuedCredentials
    timezone_was_defaulted: bool


def canonicalize_email(email: str) -> str:
    return email.strip().lower()


def resolve_timezone(proposal: str | None) -> tuple[str, bool]:
    if proposal is None:
        return "UTC", True
    candidate = proposal.strip()
    if candidate != "UTC" and IANA_TIMEZONE.fullmatch(candidate) is None:
        return "UTC", True
    try:
        ZoneInfo(candidate)
    except ZoneInfoNotFoundError:
        return "UTC", True
    return candidate, False


class RegistrationService:
    def __init__(
        self,
        password_manager: PasswordManager,
        token_issuer: TokenIssuer,
    ) -> None:
        self._password_manager = password_manager
        self._token_issuer = token_issuer

    def register(
        self,
        database_session: Session,
        request: RegistrationRequest,
    ) -> RegistrationResult:
        canonical_email = canonicalize_email(str(request.email))
        display_email = str(request.email).strip()
        timezone_name, timezone_was_defaulted = resolve_timezone(
            request.timezone_name
        )
        password_hash = self._password_manager.hash(request.password)
        now = datetime.now(UTC)

        try:
            with database_session.begin():
                user = User(
                    canonical_email=canonical_email,
                    display_email=display_email,
                    password_hash=password_hash,
                )
                database_session.add(user)
                database_session.flush()

                preference = UserPreference(
                    user_id=user.id,
                    timezone_name=timezone_name,
                    timezone_effective_at=now,
                )
                device = RegisteredDevice(
                    user_id=user.id,
                    platform=request.installation.platform,
                    installation_id=str(request.installation.installation_id),
                    app_environment=request.installation.app_environment,
                    app_version=request.installation.app_version,
                    build_version=request.installation.build_version,
                    last_seen_at=now,
                )
                database_session.add_all((preference, device))
                database_session.flush()

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
        except IntegrityError as error:
            constraint_name = getattr(error.orig, "diag", None)
            if getattr(constraint_name, "constraint_name", None) == (
                "uq_users_canonical_email"
            ):
                raise EmailAlreadyRegisteredError from error
            raise

        return RegistrationResult(
            user=user,
            preference=preference,
            device=device,
            session=session,
            credentials=credentials,
            timezone_was_defaulted=timezone_was_defaulted,
        )
