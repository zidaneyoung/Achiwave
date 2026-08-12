from datetime import date, datetime
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CompleteOccurrenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_mutation_id: UUID
    expected_occurrence_version: int = Field(ge=1)
    device_observed_at: datetime | None = None
    device_timezone_name: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("device_observed_at")
    @classmethod
    def require_observed_offset(cls, value: datetime | None) -> datetime | None:
        if value is not None and (value.tzinfo is None or value.utcoffset() is None):
            raise ValueError("Device-observed time requires an explicit offset.")
        return value

    @field_validator("device_timezone_name")
    @classmethod
    def require_iana_timezone(cls, value: str | None) -> str | None:
        if value is None:
            return None
        try:
            ZoneInfo(value)
        except (ValueError, ZoneInfoNotFoundError) as error:
            raise ValueError("Device timezone must be a recognized IANA name.") from error
        return value


class ReverseCompletionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_mutation_id: UUID
    expected_occurrence_version: int = Field(ge=1)
    reason: Literal["user_correction"] = "user_correction"


class CompletionOccurrenceResponse(BaseModel):
    id: UUID
    quest_id: UUID
    campaign_id: UUID
    status: Literal[
        "scheduled", "available", "completed", "reversed", "expired", "voided"
    ]
    record_version: int
    completed_at: datetime | None
    reversed_at: datetime | None


class CompletionRecordResponse(BaseModel):
    id: UUID
    occurrence_id: UUID
    device_id: UUID
    server_received_at: datetime
    server_processed_at: datetime
    completion_effective_date: date
    event_sequence: int
    reversed_at: datetime | None
    device_observed_at: datetime | None
    device_timezone_name: str | None
    client_time_valid: bool | None


class CompletionCampaignResponse(BaseModel):
    id: UUID
    status: Literal["active", "completed", "archived"]
    record_version: int
    completed_at: datetime | None


class ProgressEventReferenceResponse(BaseModel):
    id: UUID
    event_type: str
    event_sequence: int
    server_processed_at: datetime


class CompletionReversalResponse(BaseModel):
    id: UUID
    completion_id: UUID
    occurrence_id: UUID
    device_id: UUID
    reason: Literal["user_correction"]
    server_received_at: datetime
    server_processed_at: datetime
    event_sequence: int


class CompletionHistoryCompletionResponse(CompletionRecordResponse):
    device_id: UUID | None
    client_mutation_id: UUID | None


class CompletionHistoryReversalResponse(CompletionReversalResponse):
    device_id: UUID | None
    client_mutation_id: UUID | None
    reason: str


class CompletionHistoryItemResponse(BaseModel):
    completion: CompletionHistoryCompletionResponse
    reversal: CompletionHistoryReversalResponse | None
    progress_events: list[ProgressEventReferenceResponse]


class CompletionHistoryResponse(BaseModel):
    occurrence_id: UUID
    quest_id: UUID
    campaign_id: UUID
    items: list[CompletionHistoryItemResponse]
    total: int
    limit: int
    offset: int


class CompleteOccurrenceResponse(BaseModel):
    outcome: Literal["completed", "duplicate_completion"]
    occurrence: CompletionOccurrenceResponse
    completion: CompletionRecordResponse
    campaign: CompletionCampaignResponse
    progress_events: list[ProgressEventReferenceResponse]


class ReverseCompletionResponse(BaseModel):
    outcome: Literal["reversed", "already_reversed"]
    occurrence: CompletionOccurrenceResponse
    completion: CompletionRecordResponse
    reversal: CompletionReversalResponse
    campaign: CompletionCampaignResponse
    progress_events: list[ProgressEventReferenceResponse]
