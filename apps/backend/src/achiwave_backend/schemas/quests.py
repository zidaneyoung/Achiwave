import unicodedata
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from achiwave_backend.quest_configuration import (
    ALLOWED_QUEST_REWARD_XP,
    QuestCategory,
    QuestDifficulty,
)

QUEST_TITLE_MAX_LENGTH = 120
QUEST_DESCRIPTION_MAX_LENGTH = 4_000
LOCAL_DATE_TIME_PATTERN = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$"


def _trimmed_quest_title(value: str) -> str:
    normalized = value.strip()
    has_control = any(unicodedata.category(character) == "Cc" for character in normalized)
    if not normalized or has_control:
        raise ValueError("Quest title is invalid.")
    return normalized


def _trimmed_quest_description(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    has_control = any(
        unicodedata.category(character) == "Cc" and character not in {"\n", "\t"}
        for character in normalized
    )
    if not normalized or has_control:
        raise ValueError("Quest description is invalid.")
    return normalized


def _allowed_quest_reward(value: int) -> int:
    if value not in ALLOWED_QUEST_REWARD_XP:
        raise ValueError("Quest reward XP is not an allowed value.")
    return value


class CreateOneTimeQuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=QUEST_TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=QUEST_DESCRIPTION_MAX_LENGTH)
    category: QuestCategory | None = None
    difficulty: QuestDifficulty
    reward_xp: int = Field(default=0, strict=True, ge=0, le=2_147_483_647)
    due_local_datetime: str | None = Field(
        default=None,
        pattern=LOCAL_DATE_TIME_PATTERN,
    )
    timezone_name: str | None = Field(default=None, min_length=1, max_length=128)
    campaign_record_version: int = Field(ge=1)
    client_mutation_id: UUID

    _validate_title = field_validator("title")(_trimmed_quest_title)
    _validate_description = field_validator("description")(_trimmed_quest_description)
    _validate_reward_xp = field_validator("reward_xp")(_allowed_quest_reward)

    @model_validator(mode="after")
    def require_due_for_timezone(self) -> "CreateOneTimeQuestRequest":
        if self.timezone_name is not None and self.due_local_datetime is None:
            raise ValueError("A timezone can only be supplied with a due date.")
        return self


class UpdateOneTimeQuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=QUEST_TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=QUEST_DESCRIPTION_MAX_LENGTH)
    category: QuestCategory | None = None
    difficulty: QuestDifficulty | None = None
    reward_xp: int | None = Field(
        default=None,
        strict=True,
        ge=0,
        le=2_147_483_647,
    )
    record_version: int = Field(ge=1)
    client_mutation_id: UUID

    _validate_title = field_validator("title")(_trimmed_quest_title)
    _validate_description = field_validator("description")(_trimmed_quest_description)

    @model_validator(mode="after")
    def require_edit(self) -> "UpdateOneTimeQuestRequest":
        fields = self.model_fields_set - {"record_version", "client_mutation_id"}
        if not fields or ("title" in fields and self.title is None) or (
            "reward_xp" in fields and self.reward_xp is None
        ) or (
            "difficulty" in fields and self.difficulty is None
        ):
            raise ValueError("At least one supported quest field is required.")
        return self


class QuestTransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    record_version: int = Field(ge=1)
    client_mutation_id: UUID


class QuestOccurrenceResponse(BaseModel):
    id: UUID
    status: Literal["scheduled", "available", "completed", "reversed", "expired", "voided"]
    occurrence_local_date: date
    timezone_name: str
    available_at: datetime
    eligibility_expires_at: datetime | None
    reward_xp: int
    record_version: int


class QuestResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    campaign_record_version: int
    campaign_status: Literal["active", "completed", "archived"]
    quest_type: Literal["one_time", "recurring"]
    definition_state: Literal["active", "archived"]
    title: str
    description: str | None
    category: QuestCategory | None
    category_label: str
    difficulty: QuestDifficulty | None
    difficulty_label: str
    reward_xp: int
    display_order: int
    available_from: datetime | None
    due_at: datetime | None
    timezone_name: str | None
    due_status: Literal["none", "upcoming", "overdue", "unavailable"]
    record_version: int
    archived_at: datetime | None
    restored_at: datetime | None
    created_at: datetime
    updated_at: datetime
    occurrence: QuestOccurrenceResponse | None


class QuestConflictResponse(BaseModel):
    code: str
    message: str
    current: QuestResponse


class QuestAuthoringOptionResponse(BaseModel):
    value: str
    label: str


class QuestAuthoringOptionsResponse(BaseModel):
    categories: list[QuestAuthoringOptionResponse]
    difficulties: list[QuestAuthoringOptionResponse]
    reward_xp_values: list[int]


class QuestOrderItemRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    record_version: int = Field(ge=1)


class ReorderActiveQuestsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[QuestOrderItemRequest] = Field(min_length=1)
    campaign_record_version: int = Field(ge=1)
    client_mutation_id: UUID

    @model_validator(mode="after")
    def require_unique_quests(self) -> "ReorderActiveQuestsRequest":
        if len({item.id for item in self.items}) != len(self.items):
            raise ValueError("Each active quest must appear exactly once.")
        return self


class QuestOrderItemResponse(BaseModel):
    id: UUID
    display_order: int
    record_version: int


class QuestOrderResponse(BaseModel):
    campaign_id: UUID
    campaign_record_version: int
    items: list[QuestOrderItemResponse]


class QuestOrderConflictResponse(BaseModel):
    code: str
    message: str
    current: QuestOrderResponse
