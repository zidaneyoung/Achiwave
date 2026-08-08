import unicodedata
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

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


class CreateOneTimeQuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=QUEST_TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=QUEST_DESCRIPTION_MAX_LENGTH)
    reward_xp: int = Field(default=0, ge=0, le=2_147_483_647)
    due_local_datetime: str | None = Field(
        default=None,
        pattern=LOCAL_DATE_TIME_PATTERN,
    )
    timezone_name: str | None = Field(default=None, min_length=1, max_length=128)
    campaign_record_version: int = Field(ge=1)
    client_mutation_id: UUID

    _validate_title = field_validator("title")(_trimmed_quest_title)
    _validate_description = field_validator("description")(_trimmed_quest_description)

    @model_validator(mode="after")
    def require_due_for_timezone(self) -> "CreateOneTimeQuestRequest":
        if self.timezone_name is not None and self.due_local_datetime is None:
            raise ValueError("A timezone can only be supplied with a due date.")
        return self


class UpdateOneTimeQuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=QUEST_TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=QUEST_DESCRIPTION_MAX_LENGTH)
    reward_xp: int | None = Field(default=None, ge=0, le=2_147_483_647)
    record_version: int = Field(ge=1)
    client_mutation_id: UUID

    _validate_title = field_validator("title")(_trimmed_quest_title)
    _validate_description = field_validator("description")(_trimmed_quest_description)

    @model_validator(mode="after")
    def require_edit(self) -> "UpdateOneTimeQuestRequest":
        fields = self.model_fields_set - {"record_version", "client_mutation_id"}
        if not fields or ("title" in fields and self.title is None) or (
            "reward_xp" in fields and self.reward_xp is None
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
