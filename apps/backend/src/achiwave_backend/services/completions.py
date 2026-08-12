import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from achiwave_backend.models import (
    Campaign,
    ClientMutation,
    ProgressEvent,
    Quest,
    QuestCompletion,
    QuestCompletionReversal,
    QuestOccurrence,
    RegisteredDevice,
    User,
    UserPreference,
)
from achiwave_backend.schemas.completions import (
    CompleteOccurrenceRequest,
    CompleteOccurrenceResponse,
    CompletionCampaignResponse,
    CompletionOccurrenceResponse,
    CompletionRecordResponse,
    CompletionReversalResponse,
    ProgressEventReferenceResponse,
    ReverseCompletionRequest,
    ReverseCompletionResponse,
)
from achiwave_backend.services.campaigns import (
    InvalidCampaignStructureError,
    _derived_campaign_state,
)


class CompletionNotFoundError(Exception):
    """No owner-visible completion target matches the request."""


class CompletionMutationConflictError(Exception):
    """The mutation identifier is bound to another canonical request."""


class CompletionRejectedError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        *,
        current: dict[str, object] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.current = current

    def to_payload(self) -> dict[str, object]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "current": self.current,
            }
        }

    @classmethod
    def from_payload(cls, payload: dict[str, object]) -> "CompletionRejectedError":
        error = payload.get("error")
        if not isinstance(error, dict):
            raise CompletionMutationConflictError
        code = error.get("code")
        message = error.get("message")
        current = error.get("current")
        if (
            not isinstance(code, str)
            or not isinstance(message, str)
            or (current is not None and not isinstance(current, dict))
        ):
            raise CompletionMutationConflictError
        return cls(code, message, current=current)


def _payload_hash(payload: dict[str, object]) -> bytes:
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).digest()


def _completion_response(
    *,
    outcome: str,
    occurrence: QuestOccurrence,
    completion: QuestCompletion,
    campaign: Campaign,
    progress_events: list[ProgressEvent] | None = None,
) -> CompleteOccurrenceResponse:
    if completion.server_processed_at is None:
        raise RuntimeError("Completion result is not finalized.")
    return CompleteOccurrenceResponse(
        outcome=outcome,
        occurrence=CompletionOccurrenceResponse(
            id=occurrence.id,
            quest_id=occurrence.quest_id,
            campaign_id=occurrence.campaign_id,
            status=occurrence.occurrence_state,
            record_version=occurrence.record_version,
            completed_at=occurrence.completed_at,
            reversed_at=occurrence.reversed_at,
        ),
        completion=CompletionRecordResponse(
            id=completion.id,
            occurrence_id=completion.occurrence_id,
            device_id=completion.device_id,
            server_received_at=completion.server_received_at,
            server_processed_at=completion.server_processed_at,
            completion_effective_date=completion.completion_effective_date,
            event_sequence=completion.event_sequence,
            reversed_at=completion.reversed_at,
            device_observed_at=completion.device_observed_at,
            device_timezone_name=completion.device_timezone_name,
            client_time_valid=completion.client_time_valid,
        ),
        campaign=CompletionCampaignResponse(
            id=campaign.id,
            status=campaign.campaign_state,
            record_version=campaign.record_version,
            completed_at=campaign.completed_at,
        ),
        progress_events=[
            ProgressEventReferenceResponse(
                id=event.id,
                event_type=event.event_type,
                event_sequence=event.event_sequence,
                server_processed_at=event.server_processed_at,
            )
            for event in progress_events or []
            if event.server_processed_at is not None
        ],
    )


def _current_state(
    database_session: Session,
    occurrence: QuestOccurrence,
    campaign: Campaign,
    active_completion: QuestCompletion | None,
) -> dict[str, object]:
    related_events = database_session.scalars(
        select(ProgressEvent)
        .where(
            ProgressEvent.user_id == occurrence.user_id,
            or_(
                ProgressEvent.event_metadata["occurrence_id"].astext
                == str(occurrence.id),
                ProgressEvent.event_metadata["campaign_id"].astext
                == str(campaign.id),
            ),
        )
        .order_by(ProgressEvent.event_sequence.desc())
        .limit(20)
    ).all()
    return {
        "occurrence": {
            "id": str(occurrence.id),
            "quest_id": str(occurrence.quest_id),
            "campaign_id": str(occurrence.campaign_id),
            "status": occurrence.occurrence_state,
            "record_version": occurrence.record_version,
            "completed_at": (
                occurrence.completed_at.isoformat()
                if occurrence.completed_at is not None
                else None
            ),
            "reversed_at": (
                occurrence.reversed_at.isoformat()
                if occurrence.reversed_at is not None
                else None
            ),
        },
        "campaign": {
            "id": str(campaign.id),
            "status": campaign.campaign_state,
            "record_version": campaign.record_version,
            "completed_at": (
                campaign.completed_at.isoformat()
                if campaign.completed_at is not None
                else None
            ),
        },
        "active_completion_id": (
            str(active_completion.id) if active_completion is not None else None
        ),
        "active_completion": (
            {
                "id": str(active_completion.id),
                "event_sequence": active_completion.event_sequence,
                "reversed_at": (
                    active_completion.reversed_at.isoformat()
                    if active_completion.reversed_at is not None
                    else None
                ),
            }
            if active_completion is not None
            else None
        ),
        "progress_events": [
            {
                "id": str(event.id),
                "event_type": event.event_type,
                "event_sequence": event.event_sequence,
                "server_processed_at": (
                    event.server_processed_at.isoformat()
                    if event.server_processed_at is not None
                    else None
                ),
            }
            for event in related_events
        ],
        "event_sequence": max(
            (event.event_sequence for event in related_events),
            default=(
                active_completion.event_sequence
                if active_completion is not None
                else 0
            ),
        ),
    }


def _reversal_response(
    *,
    outcome: str,
    occurrence: QuestOccurrence,
    completion: QuestCompletion,
    reversal: QuestCompletionReversal,
    campaign: Campaign,
    progress_events: list[ProgressEvent] | None = None,
) -> ReverseCompletionResponse:
    if completion.server_processed_at is None or reversal.server_processed_at is None:
        raise RuntimeError("Reversal result is not finalized.")
    return ReverseCompletionResponse(
        outcome=outcome,
        occurrence=CompletionOccurrenceResponse(
            id=occurrence.id,
            quest_id=occurrence.quest_id,
            campaign_id=occurrence.campaign_id,
            status=occurrence.occurrence_state,
            record_version=occurrence.record_version,
            completed_at=occurrence.completed_at,
            reversed_at=occurrence.reversed_at,
        ),
        completion=CompletionRecordResponse(
            id=completion.id,
            occurrence_id=completion.occurrence_id,
            device_id=completion.device_id,
            server_received_at=completion.server_received_at,
            server_processed_at=completion.server_processed_at,
            completion_effective_date=completion.completion_effective_date,
            event_sequence=completion.event_sequence,
            reversed_at=completion.reversed_at,
            device_observed_at=completion.device_observed_at,
            device_timezone_name=completion.device_timezone_name,
            client_time_valid=completion.client_time_valid,
        ),
        reversal=CompletionReversalResponse(
            id=reversal.id,
            completion_id=reversal.completion_id,
            occurrence_id=reversal.occurrence_id,
            device_id=reversal.device_id,
            reason=reversal.reason,
            server_received_at=reversal.server_received_at,
            server_processed_at=reversal.server_processed_at,
            event_sequence=reversal.event_sequence,
        ),
        campaign=CompletionCampaignResponse(
            id=campaign.id,
            status=campaign.campaign_state,
            record_version=campaign.record_version,
            completed_at=campaign.completed_at,
        ),
        progress_events=[
            ProgressEventReferenceResponse(
                id=event.id,
                event_type=event.event_type,
                event_sequence=event.event_sequence,
                server_processed_at=event.server_processed_at,
            )
            for event in progress_events or []
            if event.server_processed_at is not None
        ],
    )


def _source_progress_events(
    database_session: Session,
    user_id: UUID,
    source_type: str,
    source_id: UUID,
) -> list[ProgressEvent]:
    return list(
        database_session.scalars(
            select(ProgressEvent)
            .where(
                ProgressEvent.user_id == user_id,
                ProgressEvent.source_type == source_type,
                ProgressEvent.source_id == source_id,
            )
            .order_by(ProgressEvent.event_sequence)
        )
    )


def _commit_permanent_rejection(
    database_session: Session,
    mutation: ClientMutation,
    error: CompletionRejectedError,
    processed_at: datetime,
) -> None:
    mutation.processing_status = "permanent_failure"
    mutation.result_type = "completion_rejection"
    mutation.result_payload = error.to_payload()
    mutation.safe_error_class = error.code
    mutation.processed_at = processed_at
    mutation.updated_at = processed_at
    try:
        database_session.commit()
    except Exception:
        database_session.rollback()
        raise
    raise error


class CompletionService:
    def complete(
        self,
        database_session: Session,
        current_user: User,
        current_device: RegisteredDevice,
        occurrence_id: UUID,
        request: CompleteOccurrenceRequest,
    ) -> CompleteOccurrenceResponse:
        user = database_session.scalar(
            select(User).where(User.id == current_user.id).with_for_update()
        )
        if user is None:
            raise RuntimeError("Authenticated user record is missing.")
        if current_device.user_id != user.id:
            raise RuntimeError("Authenticated device ownership is inconsistent.")
        received_at = datetime.now(UTC)

        payload_hash = _payload_hash(
            {
                "occurrence_id": str(occurrence_id),
                "expected_occurrence_version": request.expected_occurrence_version,
                "device_observed_at": (
                    request.device_observed_at.isoformat()
                    if request.device_observed_at is not None
                    else None
                ),
                "device_timezone_name": request.device_timezone_name,
            }
        )
        existing_mutation = database_session.scalar(
            select(ClientMutation).where(
                ClientMutation.user_id == user.id,
                ClientMutation.client_mutation_id == request.client_mutation_id,
            )
        )
        if existing_mutation is not None:
            if (
                existing_mutation.operation_type != "quest_occurrence_complete"
                or existing_mutation.target_type != "quest_occurrence"
                or existing_mutation.target_id != occurrence_id
                or existing_mutation.payload_hash != payload_hash
            ):
                raise CompletionMutationConflictError
            if (
                existing_mutation.processing_status == "permanent_failure"
                and existing_mutation.result_payload is not None
            ):
                raise CompletionRejectedError.from_payload(
                    existing_mutation.result_payload
                )
            if (
                existing_mutation.processing_status != "succeeded"
                or existing_mutation.result_payload is None
            ):
                raise CompletionMutationConflictError
            return CompleteOccurrenceResponse.model_validate(
                existing_mutation.result_payload
            )

        occurrence = database_session.scalar(
            select(QuestOccurrence)
            .where(
                QuestOccurrence.id == occurrence_id,
                QuestOccurrence.user_id == user.id,
            )
            .with_for_update()
        )
        if occurrence is None:
            raise CompletionNotFoundError
        quest = database_session.scalar(
            select(Quest).where(
                Quest.id == occurrence.quest_id,
                Quest.user_id == user.id,
                Quest.campaign_id == occurrence.campaign_id,
                Quest.quest_type == occurrence.quest_type,
                Quest.deleted_at.is_(None),
            )
        )
        campaign = database_session.scalar(
            select(Campaign)
            .where(
                Campaign.id == occurrence.campaign_id,
                Campaign.user_id == user.id,
                Campaign.deleted_at.is_(None),
            )
            .with_for_update()
        )
        if quest is None or campaign is None:
            raise CompletionNotFoundError

        active_completion = database_session.scalar(
            select(QuestCompletion).where(
                QuestCompletion.occurrence_id == occurrence.id,
                QuestCompletion.user_id == user.id,
                QuestCompletion.reversed_at.is_(None),
            )
        )
        now = received_at
        mutation = ClientMutation(
            id=uuid4(),
            user_id=user.id,
            device_id=current_device.id,
            client_mutation_id=request.client_mutation_id,
            operation_type="quest_occurrence_complete",
            payload_hash=payload_hash,
            target_type="quest_occurrence",
            target_id=occurrence.id,
            processing_status="processing",
            updated_at=now,
            first_server_received_at=received_at,
        )
        database_session.add(mutation)

        if active_completion is not None and occurrence.occurrence_state == "completed":
            progress_events = _source_progress_events(
                database_session,
                user.id,
                "quest_completion",
                active_completion.id,
            )
            response = _completion_response(
                outcome="duplicate_completion",
                occurrence=occurrence,
                completion=active_completion,
                campaign=campaign,
                progress_events=progress_events,
            )
            mutation.processing_status = "succeeded"
            mutation.result_type = "quest_completion"
            mutation.result_id = active_completion.id
            mutation.result_payload = response.model_dump(mode="json")
            mutation.processed_at = now
            database_session.commit()
            return response

        current = _current_state(
            database_session, occurrence, campaign, active_completion
        )
        if occurrence.record_version != request.expected_occurrence_version:
            error = CompletionRejectedError(
                "stale_occurrence_version",
                "The occurrence changed before completion was applied.",
                current=current,
            )
            _commit_permanent_rejection(database_session, mutation, error, now)
        if (
            campaign.campaign_state != "active"
            or quest.definition_state != "active"
            or occurrence.occurrence_state not in {"available", "reversed"}
            or occurrence.available_at > now
            or (
                occurrence.eligibility_expires_at is not None
                and occurrence.eligibility_expires_at <= now
            )
            or active_completion is not None
        ):
            error = CompletionRejectedError(
                "occurrence_not_eligible",
                "The occurrence is not eligible for completion.",
                current=current,
            )
            _commit_permanent_rejection(database_session, mutation, error, now)

        preference = database_session.get(UserPreference, user.id)
        if preference is None:
            raise RuntimeError("Active user preference record is missing.")
        try:
            effective_date = now.astimezone(
                ZoneInfo(preference.timezone_name)
            ).date()
        except ZoneInfoNotFoundError as error:
            raise RuntimeError("Saved user timezone is unavailable.") from error

        client_time_valid = (
            request.device_observed_at is not None
            and datetime(1970, 1, 1, tzinfo=UTC)
            <= request.device_observed_at.astimezone(UTC)
            <= received_at + timedelta(hours=24)
        )
        event_sequence = user.next_event_sequence
        user.next_event_sequence += 1
        user.updated_at = now
        completion = QuestCompletion(
            id=uuid4(),
            user_id=user.id,
            occurrence_id=occurrence.id,
            device_id=current_device.id,
            client_mutation_id=request.client_mutation_id,
            server_received_at=now,
            server_processed_at=now,
            completion_effective_date=effective_date,
            device_observed_at=request.device_observed_at,
            device_timezone_name=request.device_timezone_name,
            client_time_valid=(
                client_time_valid if request.device_observed_at is not None else None
            ),
            event_sequence=event_sequence,
        )
        occurrence.occurrence_state = "completed"
        occurrence.completed_at = now
        occurrence.reversed_at = None
        occurrence.record_version += 1
        occurrence.updated_at = now
        database_session.add(completion)
        completion_event = ProgressEvent(
            id=uuid4(),
            user_id=user.id,
            event_sequence=event_sequence,
            event_type="completion_accepted",
            source_type="quest_completion",
            source_id=completion.id,
            client_mutation_id=request.client_mutation_id,
            server_received_at=received_at,
            server_processed_at=received_at,
            effective_local_date=effective_date,
            rule_version=occurrence.rule_version,
            event_metadata={
                "campaign_id": str(campaign.id),
                "quest_id": str(quest.id),
                "occurrence_id": str(occurrence.id),
            },
        )
        progress_events = [completion_event]
        database_session.add(completion_event)
        database_session.flush()

        previous_campaign_state = campaign.campaign_state
        try:
            campaign.campaign_state = _derived_campaign_state(
                database_session, campaign, now
            )
        except InvalidCampaignStructureError as error:
            database_session.rollback()
            raise CompletionRejectedError(
                "campaign_structure_invalid",
                "The campaign cannot accept this completion.",
                current=current,
            ) from error
        if campaign.campaign_state != previous_campaign_state:
            campaign.record_version += 1
            campaign.updated_at = now
            if campaign.campaign_state == "completed":
                campaign.completed_at = now
                campaign.completion_reason = "quest_obligations_satisfied"
            campaign_sequence = user.next_event_sequence
            user.next_event_sequence += 1
            campaign_event = ProgressEvent(
                id=uuid4(),
                user_id=user.id,
                event_sequence=campaign_sequence,
                event_type=(
                    "campaign_completed"
                    if campaign.campaign_state == "completed"
                    else "campaign_reopened"
                ),
                source_type="quest_completion",
                source_id=completion.id,
                client_mutation_id=request.client_mutation_id,
                server_received_at=received_at,
                server_processed_at=received_at,
                rule_version=occurrence.rule_version,
                event_metadata={
                    "campaign_id": str(campaign.id),
                    "previous_state": previous_campaign_state,
                },
            )
            progress_events.append(campaign_event)
            database_session.add(campaign_event)

        processed_at = datetime.now(UTC)
        completion.server_processed_at = processed_at
        for event in progress_events:
            event.server_processed_at = processed_at
        response = _completion_response(
            outcome="completed",
            occurrence=occurrence,
            completion=completion,
            campaign=campaign,
            progress_events=progress_events,
        )
        mutation.processing_status = "succeeded"
        mutation.result_type = "quest_completion"
        mutation.result_id = completion.id
        mutation.result_payload = response.model_dump(mode="json")
        mutation.processed_at = processed_at
        mutation.updated_at = processed_at
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return response

    def reverse(
        self,
        database_session: Session,
        current_user: User,
        current_device: RegisteredDevice,
        completion_id: UUID,
        request: ReverseCompletionRequest,
    ) -> ReverseCompletionResponse:
        user = database_session.scalar(
            select(User).where(User.id == current_user.id).with_for_update()
        )
        if user is None:
            raise RuntimeError("Authenticated user record is missing.")
        if current_device.user_id != user.id:
            raise RuntimeError("Authenticated device ownership is inconsistent.")
        received_at = datetime.now(UTC)

        payload_hash = _payload_hash(
            {
                "completion_id": str(completion_id),
                "expected_occurrence_version": request.expected_occurrence_version,
                "reason": request.reason,
            }
        )
        existing_mutation = database_session.scalar(
            select(ClientMutation).where(
                ClientMutation.user_id == user.id,
                ClientMutation.client_mutation_id == request.client_mutation_id,
            )
        )
        if existing_mutation is not None:
            if (
                existing_mutation.operation_type != "quest_completion_reverse"
                or existing_mutation.target_type != "quest_completion"
                or existing_mutation.target_id != completion_id
                or existing_mutation.payload_hash != payload_hash
            ):
                raise CompletionMutationConflictError
            if (
                existing_mutation.processing_status == "permanent_failure"
                and existing_mutation.result_payload is not None
            ):
                raise CompletionRejectedError.from_payload(
                    existing_mutation.result_payload
                )
            if (
                existing_mutation.processing_status != "succeeded"
                or existing_mutation.result_payload is None
            ):
                raise CompletionMutationConflictError
            return ReverseCompletionResponse.model_validate(
                existing_mutation.result_payload
            )

        completion = database_session.scalar(
            select(QuestCompletion)
            .where(
                QuestCompletion.id == completion_id,
                QuestCompletion.user_id == user.id,
            )
            .with_for_update()
        )
        if completion is None:
            raise CompletionNotFoundError
        occurrence = database_session.scalar(
            select(QuestOccurrence)
            .where(
                QuestOccurrence.id == completion.occurrence_id,
                QuestOccurrence.user_id == user.id,
            )
            .with_for_update()
        )
        if occurrence is None:
            raise CompletionNotFoundError
        quest = database_session.scalar(
            select(Quest).where(
                Quest.id == occurrence.quest_id,
                Quest.user_id == user.id,
                Quest.campaign_id == occurrence.campaign_id,
                Quest.quest_type == occurrence.quest_type,
            )
        )
        campaign = database_session.scalar(
            select(Campaign)
            .where(
                Campaign.id == occurrence.campaign_id,
                Campaign.user_id == user.id,
            )
            .with_for_update()
        )
        if quest is None or campaign is None:
            raise CompletionNotFoundError

        existing_reversal = database_session.scalar(
            select(QuestCompletionReversal).where(
                QuestCompletionReversal.completion_id == completion.id,
                QuestCompletionReversal.user_id == user.id,
                QuestCompletionReversal.occurrence_id == occurrence.id,
            )
        )
        now = received_at
        mutation = ClientMutation(
            id=uuid4(),
            user_id=user.id,
            device_id=current_device.id,
            client_mutation_id=request.client_mutation_id,
            operation_type="quest_completion_reverse",
            payload_hash=payload_hash,
            target_type="quest_completion",
            target_id=completion.id,
            processing_status="processing",
            updated_at=now,
            first_server_received_at=received_at,
        )
        database_session.add(mutation)
        if (
            existing_reversal is not None
            and completion.reversed_at is not None
            and occurrence.occurrence_state == "reversed"
        ):
            progress_events = _source_progress_events(
                database_session,
                user.id,
                "quest_completion_reversal",
                existing_reversal.id,
            )
            response = _reversal_response(
                outcome="already_reversed",
                occurrence=occurrence,
                completion=completion,
                reversal=existing_reversal,
                campaign=campaign,
                progress_events=progress_events,
            )
            mutation.processing_status = "succeeded"
            mutation.result_type = "quest_completion_reversal"
            mutation.result_id = existing_reversal.id
            mutation.result_payload = response.model_dump(mode="json")
            mutation.processed_at = now
            database_session.commit()
            return response

        current = _current_state(
            database_session,
            occurrence,
            campaign,
            completion if completion.reversed_at is None else None,
        )
        if occurrence.record_version != request.expected_occurrence_version:
            error = CompletionRejectedError(
                "stale_occurrence_version",
                "The occurrence changed before reversal was applied.",
                current=current,
            )
            _commit_permanent_rejection(database_session, mutation, error, now)
        if (
            completion.reversed_at is not None
            or existing_reversal is not None
            or occurrence.occurrence_state != "completed"
            or occurrence.expired_at is not None
            or occurrence.voided_at is not None
        ):
            error = CompletionRejectedError(
                "completion_not_active",
                "The completion is not active and cannot be reversed.",
                current=current,
            )
            _commit_permanent_rejection(database_session, mutation, error, now)

        event_sequence = user.next_event_sequence
        user.next_event_sequence += 1
        user.updated_at = now
        reversal = QuestCompletionReversal(
            id=uuid4(),
            user_id=user.id,
            occurrence_id=occurrence.id,
            completion_id=completion.id,
            device_id=current_device.id,
            client_mutation_id=request.client_mutation_id,
            reason=request.reason,
            server_received_at=now,
            server_processed_at=now,
            event_sequence=event_sequence,
        )
        completion.reversed_at = now
        occurrence.occurrence_state = "reversed"
        occurrence.reversed_at = now
        occurrence.record_version += 1
        occurrence.updated_at = now
        database_session.add(reversal)
        reversal_event = ProgressEvent(
            id=uuid4(),
            user_id=user.id,
            event_sequence=event_sequence,
            event_type="completion_reversed",
            source_type="quest_completion_reversal",
            source_id=reversal.id,
            client_mutation_id=request.client_mutation_id,
            server_received_at=received_at,
            server_processed_at=received_at,
            effective_local_date=completion.completion_effective_date,
            rule_version=occurrence.rule_version,
            event_metadata={
                "campaign_id": str(campaign.id),
                "quest_id": str(quest.id),
                "occurrence_id": str(occurrence.id),
                "completion_id": str(completion.id),
            },
        )
        progress_events = [reversal_event]
        database_session.add(reversal_event)
        database_session.flush()

        if campaign.campaign_state != "archived":
            previous_campaign_state = campaign.campaign_state
            try:
                campaign.campaign_state = _derived_campaign_state(
                    database_session, campaign, now
                )
            except InvalidCampaignStructureError as error:
                database_session.rollback()
                raise CompletionRejectedError(
                    "campaign_structure_invalid",
                    "The campaign cannot accept this reversal.",
                    current=current,
                ) from error
            if campaign.campaign_state != previous_campaign_state:
                campaign.record_version += 1
                campaign.updated_at = now
                campaign_sequence = user.next_event_sequence
                user.next_event_sequence += 1
                campaign_event = ProgressEvent(
                    id=uuid4(),
                    user_id=user.id,
                    event_sequence=campaign_sequence,
                    event_type=(
                        "campaign_completed"
                        if campaign.campaign_state == "completed"
                        else "campaign_reopened"
                    ),
                    source_type="quest_completion_reversal",
                    source_id=reversal.id,
                    client_mutation_id=request.client_mutation_id,
                    server_received_at=received_at,
                    server_processed_at=received_at,
                    rule_version=occurrence.rule_version,
                    event_metadata={
                        "campaign_id": str(campaign.id),
                        "previous_state": previous_campaign_state,
                    },
                )
                progress_events.append(campaign_event)
                database_session.add(campaign_event)

        processed_at = datetime.now(UTC)
        reversal.server_processed_at = processed_at
        for event in progress_events:
            event.server_processed_at = processed_at
        response = _reversal_response(
            outcome="reversed",
            occurrence=occurrence,
            completion=completion,
            reversal=reversal,
            campaign=campaign,
            progress_events=progress_events,
        )
        mutation.processing_status = "succeeded"
        mutation.result_type = "quest_completion_reversal"
        mutation.result_id = reversal.id
        mutation.result_payload = response.model_dump(mode="json")
        mutation.processed_at = processed_at
        mutation.updated_at = processed_at
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return response
