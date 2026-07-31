import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt

from achiwave_backend.config import Settings


@dataclass(frozen=True, slots=True)
class IssuedCredentials:
    access_token: str
    refresh_token: str
    refresh_token_digest: bytes
    access_expires_at: datetime
    refresh_expires_at: datetime


class TokenIssuer:
    def __init__(self, settings: Settings) -> None:
        self._signing_key = settings.require_access_token_signing_key()
        self._algorithm = settings.access_token_algorithm
        self._issuer = settings.access_token_issuer
        self._audience = settings.access_token_audience
        self._access_lifetime = timedelta(
            seconds=settings.access_token_lifetime_seconds
        )
        self._refresh_lifetime = timedelta(
            seconds=settings.refresh_token_lifetime_seconds
        )

    def issue(
        self,
        *,
        user_id: UUID,
        session_id: UUID,
        now: datetime | None = None,
    ) -> IssuedCredentials:
        issued_at = now or datetime.now(UTC)
        access_expires_at = issued_at + self._access_lifetime
        refresh_expires_at = issued_at + self._refresh_lifetime
        access_token = jwt.encode(
            {
                "sub": str(user_id),
                "sid": str(session_id),
                "iat": issued_at,
                "exp": access_expires_at,
                "jti": str(uuid4()),
                "iss": self._issuer,
                "aud": self._audience,
            },
            self._signing_key,
            algorithm=self._algorithm,
        )
        refresh_token = secrets.token_urlsafe(64)
        return IssuedCredentials(
            access_token=access_token,
            refresh_token=refresh_token,
            refresh_token_digest=hashlib.sha256(
                refresh_token.encode("utf-8")
            ).digest(),
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )
