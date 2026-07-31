from argon2 import PasswordHasher
from argon2.low_level import Type

from achiwave_backend.config import Settings


class PasswordPolicyError(ValueError):
    """Password does not satisfy the configured length boundary."""


class PasswordManager:
    def __init__(self, settings: Settings) -> None:
        self._minimum_length = settings.password_min_length
        self._maximum_length = settings.password_max_length
        self._hasher = PasswordHasher(type=Type.ID)

    def hash(self, password: str) -> str:
        length = len(password)
        if length < self._minimum_length or length > self._maximum_length:
            raise PasswordPolicyError(
                f"Password must contain between {self._minimum_length} and "
                f"{self._maximum_length} Unicode characters."
            )
        return self._hasher.hash(password)
