import hmac
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from achiwave_backend.auth.tokens import (
    AccessTokenExpiredError,
    InvalidAccessTokenError,
    TokenVerifier,
    digest_refresh_token,
)
from achiwave_backend.models import DeviceSession


class LogoutCredentialRequiredError(ValueError):
    """Neither a usable bearer nor refresh credential was supplied."""


class LogoutSessionNotFoundError(ValueError):
    """Credential does not identify a retained session."""


class LogoutService:
    def __init__(self, token_verifier: TokenVerifier) -> None:
        self._token_verifier = token_verifier

    @staticmethod
    def _revoke(
        session: DeviceSession,
        now: datetime,
        reason: str,
    ) -> None:
        if session.session_state != "active":
            return
        session.session_state = "revoked"
        session.revoked_at = now
        session.revocation_reason = reason
        session.record_version += 1
        session.updated_at = now

    def logout(
        self,
        database_session: Session,
        *,
        access_token: str | None,
        refresh_token: str | None,
    ) -> None:
        if access_token is None and refresh_token is None:
            raise LogoutCredentialRequiredError
        now = datetime.now(UTC)
        access_expired = False
        claims = None
        if access_token is not None:
            try:
                claims = self._token_verifier.verify(access_token)
            except AccessTokenExpiredError:
                access_expired = True
            except InvalidAccessTokenError:
                raise

        with database_session.begin():
            target_session: DeviceSession | None = None
            if claims is not None:
                target_session = database_session.scalar(
                    select(DeviceSession)
                    .where(
                        DeviceSession.id == claims.session_id,
                        DeviceSession.user_id == claims.user_id,
                    )
                    .with_for_update()
                )
                if target_session is None:
                    raise LogoutSessionNotFoundError
            elif refresh_token is not None:
                supplied_digest = digest_refresh_token(refresh_token)
                target_session = database_session.scalar(
                    select(DeviceSession)
                    .where(DeviceSession.credential_digest == supplied_digest)
                    .with_for_update()
                )
                if (
                    target_session is None
                    or target_session.credential_digest is None
                    or not hmac.compare_digest(
                        target_session.credential_digest,
                        supplied_digest,
                    )
                ):
                    raise LogoutSessionNotFoundError
            elif access_expired:
                raise AccessTokenExpiredError

            if target_session is None:
                raise LogoutCredentialRequiredError
            if target_session.session_state == "replaced":
                database_session.execute(
                    update(DeviceSession)
                    .where(
                        DeviceSession.user_id == target_session.user_id,
                        DeviceSession.device_id == target_session.device_id,
                        DeviceSession.session_state == "active",
                    )
                    .values(
                        session_state="revoked",
                        revoked_at=now,
                        revocation_reason="logout_replaced_credential",
                        record_version=DeviceSession.record_version + 1,
                        updated_at=now,
                    )
                )
            else:
                self._revoke(target_session, now, "user_logout")
