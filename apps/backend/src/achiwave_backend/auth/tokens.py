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


@dataclass(frozen=True, slots=True)
class AccessTokenClaims:
    user_id: UUID
    session_id: UUID
    issued_at: datetime
    expires_at: datetime
    token_id: UUID


class InvalidAccessTokenError(ValueError):
    """Bearer token failed signature, claim, or shape validation."""


class AccessTokenExpiredError(InvalidAccessTokenError):
    """Bearer token is valid apart from its elapsed expiration."""


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
            refresh_token_digest=digest_refresh_token(refresh_token),
            access_expires_at=access_expires_at,
            refresh_expires_at=refresh_expires_at,
        )


class TokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._signing_key = settings.require_access_token_signing_key()
        self._algorithm = settings.access_token_algorithm
        self._issuer = settings.access_token_issuer
        self._audience = settings.access_token_audience

    def verify(self, token: str) -> AccessTokenClaims:
        try:
            payload = jwt.decode(
                token,
                self._signing_key,
                algorithms=[self._algorithm],
                issuer=self._issuer,
                audience=self._audience,
                options={
                    "require": ["sub", "sid", "iat", "exp", "jti", "iss", "aud"]
                },
            )
        except jwt.ExpiredSignatureError as error:
            raise AccessTokenExpiredError from error
        except jwt.InvalidTokenError as error:
            raise InvalidAccessTokenError from error

        try:
            return AccessTokenClaims(
                user_id=UUID(payload["sub"]),
                session_id=UUID(payload["sid"]),
                issued_at=datetime.fromtimestamp(payload["iat"], tz=UTC),
                expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
                token_id=UUID(payload["jti"]),
            )
        except (KeyError, TypeError, ValueError, OSError) as error:
            raise InvalidAccessTokenError from error


def digest_refresh_token(refresh_token: str) -> bytes:
    return hashlib.sha256(refresh_token.encode("utf-8")).digest()
