from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompleteOccurrenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    client_mutation_id: UUID
    expected_occurrence_version: int = Field(ge=1)


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
    server_received_at: datetime
    server_processed_at: datetime
    completion_effective_date: date
    event_sequence: int
    reversed_at: datetime | None


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
    reason: Literal["user_correction"]
    server_received_at: datetime
    server_processed_at: datetime
    event_sequence: int


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
