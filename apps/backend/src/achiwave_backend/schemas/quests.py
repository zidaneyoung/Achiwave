import unicodedata
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

QUEST_TITLE_MAX_LENGTH = 120


def _trimmed_quest_title(value: str) -> str:
    normalized = value.strip()
    has_control = any(unicodedata.category(character) == "Cc" for character in normalized)
    if not normalized or has_control:
        raise ValueError("Quest title is invalid.")
    return normalized


class CreateOneTimeQuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=QUEST_TITLE_MAX_LENGTH)
    reward_xp: int = Field(default=0, ge=0, le=2_147_483_647)
    campaign_record_version: int = Field(ge=1)
    client_mutation_id: UUID

    _validate_title = field_validator("title")(_trimmed_quest_title)


class UpdateOneTimeQuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=QUEST_TITLE_MAX_LENGTH)
    reward_xp: int | None = Field(default=None, ge=0, le=2_147_483_647)
    record_version: int = Field(ge=1)
    client_mutation_id: UUID

    _validate_title = field_validator("title")(_trimmed_quest_title)

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
