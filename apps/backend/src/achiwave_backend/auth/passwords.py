from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from argon2.low_level import Type

from achiwave_backend.config import Settings


class PasswordPolicyError(ValueError):
    """Password does not satisfy the configured length boundary."""


class PasswordManager:
    def __init__(self, settings: Settings) -> None:
        self._minimum_length = settings.password_min_length
        self._maximum_length = settings.password_max_length
        self._hasher = PasswordHasher(type=Type.ID)
        self._dummy_hash = self._hasher.hash(
            "achiwave-dummy-authentication-password"
        )

    def hash(self, password: str) -> str:
        length = len(password)
        if length < self._minimum_length or length > self._maximum_length:
            raise PasswordPolicyError(
                f"Password must contain between {self._minimum_length} and "
                f"{self._maximum_length} Unicode characters."
            )
        return self._hasher.hash(password)

    def verify(
        self,
        password: str,
        password_hash: str | None,
    ) -> tuple[bool, str | None]:
        candidate_hash = password_hash or self._dummy_hash
        try:
            valid = self._hasher.verify(candidate_hash, password)
        except (VerificationError, InvalidHashError):
            return False, None
        if not valid or password_hash is None:
            return False, None
        replacement = (
            self._hasher.hash(password)
            if self._hasher.check_needs_rehash(password_hash)
            else None
        )
        return True, replacement
