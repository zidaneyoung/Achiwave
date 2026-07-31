"""Explicit SQLAlchemy model registration for Alembic metadata."""

from achiwave_backend.models.registered_device import RegisteredDevice
from achiwave_backend.models.user import User
from achiwave_backend.models.user_preference import UserPreference

__all__ = ["RegisteredDevice", "User", "UserPreference"]
