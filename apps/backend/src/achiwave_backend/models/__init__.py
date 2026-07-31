"""Explicit SQLAlchemy model registration for Alembic metadata."""

from achiwave_backend.models.campaign import Campaign
from achiwave_backend.models.device_session import DeviceSession
from achiwave_backend.models.push_token import PushToken
from achiwave_backend.models.quest import Quest
from achiwave_backend.models.quest_occurrence import QuestOccurrence
from achiwave_backend.models.quest_recurrence import QuestRecurrence
from achiwave_backend.models.registered_device import RegisteredDevice
from achiwave_backend.models.user import User
from achiwave_backend.models.user_preference import UserPreference

__all__ = [
    "Campaign",
    "DeviceSession",
    "PushToken",
    "Quest",
    "QuestOccurrence",
    "QuestRecurrence",
    "RegisteredDevice",
    "User",
    "UserPreference",
]
