import hmac
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from achiwave_backend.auth.tokens import (
    IssuedCredentials,
    TokenIssuer,
    digest_refresh_token,
)
from achiwave_backend.models import DeviceSession, RegisteredDevice, User
from achiwave_backend.schemas.auth import RefreshRequest


class InvalidRefreshTokenError(ValueError):
    """Refresh credential or public device context is invalid."""


class SessionExpiredError(ValueError):
    """Refresh session reached its server expiry."""


class SessionRevokedError(ValueError):
    """Refresh session is no longer active."""


class RefreshTokenReuseError(ValueError):
    """A replaced refresh credential was submitted again."""


class RefreshDeviceRevokedError(ValueError):
    """Registered device is no longer active."""


class RefreshAccountUnavailableError(ValueError):
    """Account no longer permits authenticated sessions."""


@dataclass(frozen=True, slots=True)
class RefreshResult:
    session: DeviceSession
    credentials: IssuedCredentials


class RefreshService:
    def __init__(self, token_issuer: TokenIssuer) -> None:
        self._token_issuer = token_issuer

    @staticmethod
    def _revoke_active_sessions(
        database_session: Session,
        *,
        user_id,
        now: datetime,
        reason: str,
        device_id=None,
    ) -> None:
        filters = [
            DeviceSession.user_id == user_id,
            DeviceSession.session_state == "active",
        ]
        if device_id is not None:
            filters.append(DeviceSession.device_id == device_id)
        database_session.execute(
            update(DeviceSession)
            .where(*filters)
            .values(
                session_state="revoked",
                revoked_at=now,
                revocation_reason=reason,
                record_version=DeviceSession.record_version + 1,
                updated_at=now,
            )
        )

    def refresh(
        self,
        database_session: Session,
        request: RefreshRequest,
    ) -> RefreshResult:
        now = datetime.now(UTC)
        supplied_digest = digest_refresh_token(request.refresh_token)
        failure: Exception | None = None
        result: RefreshResult | None = None

        with database_session.begin():
            current_session = database_session.scalar(
                select(DeviceSession)
                .where(DeviceSession.credential_digest == supplied_digest)
                .with_for_update()
            )
            if current_session is None or current_session.credential_digest is None:
                failure = InvalidRefreshTokenError()
            elif not hmac.compare_digest(
                current_session.credential_digest,
                supplied_digest,
            ):
                failure = InvalidRefreshTokenError()
            else:
                user = database_session.get(User, current_session.user_id)
                device = database_session.get(
                    RegisteredDevice,
                    current_session.device_id,
                )
                if user is None or device is None:
                    failure = InvalidRefreshTokenError()
                elif current_session.session_state == "replaced":
                    self._revoke_active_sessions(
                        database_session,
                        user_id=current_session.user_id,
                        device_id=current_session.device_id,
                        now=now,
                        reason="refresh_token_reuse",
                    )
                    failure = RefreshTokenReuseError()
                elif current_session.session_state == "revoked":
                    failure = SessionRevokedError()
                elif (
                    current_session.session_state == "expired"
                    or current_session.expires_at <= now
                ):
                    if current_session.session_state == "active":
                        current_session.session_state = "expired"
                        current_session.record_version += 1
                        current_session.updated_at = now
                    failure = SessionExpiredError()
                elif user.account_state != "active":
                    self._revoke_active_sessions(
                        database_session,
                        user_id=user.id,
                        now=now,
                        reason="account_unavailable",
                    )
                    failure = RefreshAccountUnavailableError()
                elif device.device_state != "active":
                    self._revoke_active_sessions(
                        database_session,
                        user_id=user.id,
                        device_id=device.id,
                        now=now,
                        reason="device_unavailable",
                    )
                    failure = RefreshDeviceRevokedError()
                elif (
                    device.platform != request.installation.platform
                    or device.installation_id
                    != str(request.installation.installation_id)
                    or device.app_environment
                    != request.installation.app_environment
                ):
                    failure = InvalidRefreshTokenError()
                else:
                    replacement = DeviceSession(
                        id=uuid4(),
                        user_id=user.id,
                        device_id=device.id,
                        expires_at=now,
                    )
                    credentials = self._token_issuer.issue(
                        user_id=user.id,
                        session_id=replacement.id,
                        now=now,
                    )
                    replacement.expires_at = credentials.refresh_expires_at
                    replacement.credential_digest = (
                        credentials.refresh_token_digest
                    )
                    database_session.add(replacement)
                    database_session.flush()

                    current_session.session_state = "replaced"
                    current_session.replaced_at = now
                    current_session.replaced_by_session_id = replacement.id
                    current_session.record_version += 1
                    current_session.updated_at = now
                    device.last_seen_at = now
                    device.updated_at = now
                    device.record_version += 1
                    database_session.flush()
                    result = RefreshResult(
                        session=replacement,
                        credentials=credentials,
                    )

        if failure is not None:
            raise failure
        if result is None:
            raise RuntimeError("Refresh transaction produced no result.")
        return result
