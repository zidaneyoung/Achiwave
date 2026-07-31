"""Explicit SQLAlchemy model registration for Alembic metadata."""

from achiwave_backend.models.campaign import Campaign
from achiwave_backend.models.achievement_definition import AchievementDefinition
from achiwave_backend.models.achievement_rule import AchievementRule
from achiwave_backend.models.client_mutation import ClientMutation
from achiwave_backend.models.device_session import DeviceSession
from achiwave_backend.models.level_definition import LevelDefinition
from achiwave_backend.models.progress_event import ProgressEvent
from achiwave_backend.models.push_token import PushToken
from achiwave_backend.models.quest import Quest
from achiwave_backend.models.quest_completion import (
    QuestCompletion,
    QuestCompletionReversal,
)
from achiwave_backend.models.quest_occurrence import QuestOccurrence
from achiwave_backend.models.quest_recurrence import QuestRecurrence
from achiwave_backend.models.registered_device import RegisteredDevice
from achiwave_backend.models.synchronization_operation import SynchronizationOperation
from achiwave_backend.models.streak import Streak, StreakDay, StreakDaySource
from achiwave_backend.models.user import User
from achiwave_backend.models.user_preference import UserPreference
from achiwave_backend.models.xp_ledger_entry import XpLedgerEntry

__all__ = [
    "AchievementDefinition",
    "AchievementRule",
    "Campaign",
    "ClientMutation",
    "DeviceSession",
    "LevelDefinition",
    "ProgressEvent",
    "PushToken",
    "Quest",
    "QuestCompletion",
    "QuestCompletionReversal",
    "QuestOccurrence",
    "QuestRecurrence",
    "RegisteredDevice",
    "SynchronizationOperation",
    "Streak",
    "StreakDay",
    "StreakDaySource",
    "User",
    "UserPreference",
    "XpLedgerEntry",
]
