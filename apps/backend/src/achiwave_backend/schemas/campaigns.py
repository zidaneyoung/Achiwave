import unicodedata
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

CAMPAIGN_TITLE_MAX_LENGTH = 120
CAMPAIGN_DESCRIPTION_MAX_LENGTH = 4_000


def _contains_unsupported_control_characters(value: str) -> bool:
    return any(
        unicodedata.category(character) == "Cc" and character not in {"\n", "\t"}
        for character in value
    )


def _trimmed_title(value: str) -> str:
    normalized = value.strip()
    if not normalized or _contains_unsupported_control_characters(normalized):
        raise ValueError("Campaign title is invalid.")
    return normalized


def _trimmed_description(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized or _contains_unsupported_control_characters(normalized):
        raise ValueError("Campaign description is invalid.")
    return normalized


class CampaignResponse(BaseModel):
    id: UUID
    title: str
    description: str | None
    display_order: int
    status: Literal["active", "completed", "archived"]
    record_version: int
    completed_at: datetime | None
    archived_at: datetime | None
    restored_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CampaignQuestSummaryResponse(BaseModel):
    active: int
    archived: int
    total: int


class CampaignListItemResponse(CampaignResponse):
    quest_summary: CampaignQuestSummaryResponse


class CampaignListResponse(BaseModel):
    items: list[CampaignListItemResponse]
    total: int
    limit: int
    offset: int


class CampaignQuestResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    quest_type: Literal["one_time", "recurring"]
    definition_state: Literal["active", "archived"]
    status: Literal[
        "active",
        "archived",
        "scheduled",
        "available",
        "completed",
        "reversed",
        "expired",
        "voided",
    ]
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


class CampaignDetailResponse(CampaignResponse):
    quest_summary: CampaignQuestSummaryResponse
    quests: list[CampaignQuestResponse]


class CreateCampaignRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=CAMPAIGN_TITLE_MAX_LENGTH)
    description: str | None = Field(
        default=None,
        max_length=CAMPAIGN_DESCRIPTION_MAX_LENGTH,
    )
    client_mutation_id: UUID

    _validate_title = field_validator("title")(_trimmed_title)
    _validate_description = field_validator("description")(_trimmed_description)
