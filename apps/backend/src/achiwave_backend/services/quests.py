import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from importlib.metadata import PackageNotFoundError, version
from typing import Any
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from achiwave_backend.models import (
    Campaign,
    ClientMutation,
    Quest,
    QuestOccurrence,
    ProgressEvent,
    User,
    UserPreference,
)
from achiwave_backend.quest_configuration import ALLOWED_QUEST_REWARD_XP
from achiwave_backend.schemas.quests import (
    CreateOneTimeQuestRequest,
    QuestTransitionRequest,
    ReorderActiveQuestsRequest,
    UpdateOneTimeQuestRequest,
)
from achiwave_backend.services.campaigns import _derived_campaign_state
from achiwave_backend.services.preferences import InvalidTimezoneError, validate_timezone_name


class CampaignUnavailableError(Exception):
    """The owner-visible campaign cannot accept a new quest."""


class QuestMutationConflictError(Exception):
    """A mutation identifier is already bound to another payload."""


class StaleCampaignVersionError(Exception):
    def __init__(self, campaign: Campaign) -> None:
        self.campaign = campaign


class QuestNotFoundError(Exception):
    """No owner-visible one-time quest matches the supplied identifier."""


class InvalidQuestScheduleError(Exception):
    """A supplied local due date cannot produce an accepted future instant."""


class InvalidQuestRewardError(Exception):
    """A changed quest reward is outside the accepted authoring choices."""


class InvalidQuestOrderError(Exception):
    """A reorder payload does not exactly describe the owner's active quests."""


class StaleQuestOrderError(Exception):
    def __init__(self, result: "QuestOrderResult") -> None:
        self.result = result


class StaleQuestVersionError(Exception):
    def __init__(self, result: "QuestResult") -> None:
        self.result = result


class QuestResult:
    def __init__(
        self,
        quest: Quest,
        occurrence: QuestOccurrence,
        campaign: Campaign,
    ) -> None:
        self.quest = quest
        self.occurrence = occurrence
        self.campaign = campaign


@dataclass(frozen=True)
class QuestOrderItemResult:
    id: UUID
    display_order: int
    record_version: int


@dataclass(frozen=True)
class QuestOrderResult:
    campaign_id: UUID
    campaign_record_version: int
    items: tuple[QuestOrderItemResult, ...]

    @classmethod
    def from_models(cls, campaign: Campaign, quests: list[Quest]) -> "QuestOrderResult":
        ordered_quests = sorted(
            quests, key=lambda quest: (quest.display_order, quest.id)
        )
        return cls(
            campaign_id=campaign.id,
            campaign_record_version=campaign.record_version,
            items=tuple(
                QuestOrderItemResult(
                    id=quest.id,
                    display_order=quest.display_order,
                    record_version=quest.record_version,
                )
                for quest in ordered_quests
            ),
        )

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "QuestOrderResult":
        return cls(
            campaign_id=UUID(payload["campaign_id"]),
            campaign_record_version=int(payload["campaign_record_version"]),
            items=tuple(
                QuestOrderItemResult(
                    id=UUID(item["id"]),
                    display_order=int(item["display_order"]),
                    record_version=int(item["record_version"]),
                )
                for item in payload["items"]
            ),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "campaign_id": str(self.campaign_id),
            "campaign_record_version": self.campaign_record_version,
            "items": [
                {
                    "id": str(item.id),
                    "display_order": item.display_order,
                    "record_version": item.record_version,
                }
                for item in self.items
            ],
        }


def _payload_hash(payload: dict[str, object]) -> bytes:
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).digest()


def _timezone_data_version() -> str:
    try:
        return f"tzdata-{version('tzdata')}"
    except PackageNotFoundError:
        return "system"


def _valid_local_candidate(
    local_value: datetime,
    timezone: ZoneInfo,
    fold: int,
) -> datetime | None:
    candidate = local_value.replace(tzinfo=timezone, fold=fold)
    resolved = candidate.astimezone(UTC)
    round_trip = resolved.astimezone(timezone).replace(tzinfo=None)
    return resolved if round_trip == local_value else None


def _resolve_local_due(local_value: str, timezone: ZoneInfo) -> datetime:
    try:
        requested = datetime.strptime(local_value, "%Y-%m-%dT%H:%M")
    except ValueError as error:
        raise InvalidQuestScheduleError from error

    # fold=0 selects the earlier offset during a fall-back overlap.
    resolved = _valid_local_candidate(requested, timezone, fold=0)
    if resolved is not None:
        return resolved

    # A spring-forward gap resolves to the first valid local minute after the gap.
    candidate = requested
    for _ in range(180):
        candidate += timedelta(minutes=1)
        resolved = _valid_local_candidate(candidate, timezone, fold=0)
        if resolved is not None:
            return resolved
    raise InvalidQuestScheduleError


def quest_due_status(
    quest: Quest,
    occurrence_status: str,
    campaign_status: str,
    *,
    now: datetime | None = None,
) -> str:
    if quest.due_at is None:
        return "none"
    if (
        quest.definition_state == "archived"
        or campaign_status == "archived"
        or occurrence_status in {"completed", "reversed", "expired", "voided"}
    ):
        return "unavailable"
    return "overdue" if quest.due_at <= (now or datetime.now(UTC)) else "upcoming"


class QuestService:
    def reorder_active(
        self,
        database_session: Session,
        current_user: User,
        campaign_id: UUID,
        request: ReorderActiveQuestsRequest,
    ) -> QuestOrderResult:
        user = database_session.scalar(
            select(User).where(User.id == current_user.id).with_for_update()
        )
        if user is None:
            raise RuntimeError("Authenticated user record is missing.")
        payload_hash = _payload_hash(
            {
                "campaign_id": str(campaign_id),
                "campaign_record_version": request.campaign_record_version,
                "items": [
                    {"id": str(item.id), "record_version": item.record_version}
                    for item in request.items
                ],
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
                existing_mutation.operation_type != "active_quest_reorder"
                or existing_mutation.target_id != campaign_id
                or existing_mutation.payload_hash != payload_hash
                or existing_mutation.result_id != campaign_id
                or existing_mutation.result_payload is None
            ):
                raise QuestMutationConflictError
            return QuestOrderResult.from_payload(existing_mutation.result_payload)

        campaign = database_session.scalar(
            select(Campaign)
            .where(
                Campaign.id == campaign_id,
                Campaign.user_id == user.id,
                Campaign.campaign_state != "archived",
                Campaign.deleted_at.is_(None),
            )
            .with_for_update()
        )
        if campaign is None:
            raise CampaignUnavailableError
        quests = list(
            database_session.scalars(
                select(Quest)
                .where(
                    Quest.user_id == user.id,
                    Quest.campaign_id == campaign.id,
                    Quest.definition_state == "active",
                    Quest.deleted_at.is_(None),
                )
                .order_by(Quest.id)
                .with_for_update()
            )
        )
        result = QuestOrderResult.from_models(campaign, quests)

        requested_ids = [item.id for item in request.items]
        quests_by_id = {quest.id: quest for quest in quests}
        if (
            len(requested_ids) != len(quests)
            or len(set(requested_ids)) != len(requested_ids)
            or set(requested_ids) != set(quests_by_id)
        ):
            raise InvalidQuestOrderError
        if campaign.record_version != request.campaign_record_version:
            raise StaleQuestOrderError(result)
        requested_versions = {item.id: item.record_version for item in request.items}
        if any(
            quest.record_version != requested_versions[quest.id]
            for quest in quests
        ):
            raise StaleQuestOrderError(result)

        now = datetime.now(UTC)
        changed = False
        for display_order, quest_id in enumerate(requested_ids):
            quest = quests_by_id[quest_id]
            if quest.display_order != display_order:
                quest.display_order = display_order
                quest.record_version += 1
                quest.updated_at = now
                changed = True
        if changed:
            campaign.record_version += 1
            campaign.updated_at = now
        result = QuestOrderResult.from_models(campaign, quests)
        database_session.add(
            ClientMutation(
                id=uuid4(),
                user_id=user.id,
                client_mutation_id=request.client_mutation_id,
                operation_type="active_quest_reorder",
                payload_hash=payload_hash,
                target_type="campaign",
                target_id=campaign.id,
                processing_status="succeeded",
                result_type="campaign",
                result_id=campaign.id,
                result_payload=result.to_payload(),
                processed_at=now,
                updated_at=now,
            )
        )
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return result

    def _transition_one_time(
        self,
        database_session: Session,
        current_user: User,
        quest_id: UUID,
        request: QuestTransitionRequest,
        *,
        restore: bool,
    ) -> QuestResult:
        user = database_session.scalar(
            select(User).where(User.id == current_user.id).with_for_update()
        )
        if user is None:
            raise RuntimeError("Authenticated user record is missing.")
        quest = database_session.scalar(
            select(Quest)
            .where(
                Quest.id == quest_id,
                Quest.user_id == user.id,
                Quest.quest_type == "one_time",
                Quest.deleted_at.is_(None),
            )
            .with_for_update()
        )
        if quest is None:
            raise QuestNotFoundError
        campaign = database_session.scalar(
            select(Campaign)
            .where(
                Campaign.id == quest.campaign_id,
                Campaign.user_id == user.id,
                Campaign.deleted_at.is_(None),
            )
            .with_for_update()
        )
        occurrence = database_session.scalar(
            select(QuestOccurrence).where(
                QuestOccurrence.quest_id == quest.id,
                QuestOccurrence.user_id == user.id,
            )
        )
        if campaign is None or occurrence is None or campaign.campaign_state == "archived":
            raise QuestNotFoundError
        operation = "one_time_quest_restore" if restore else "one_time_quest_archive"
        payload_hash = _payload_hash(
            {"quest_id": str(quest.id), "record_version": request.record_version}
        )
        existing_mutation = database_session.scalar(
            select(ClientMutation).where(
                ClientMutation.user_id == user.id,
                ClientMutation.client_mutation_id == request.client_mutation_id,
            )
        )
        if existing_mutation is not None:
            if (
                existing_mutation.operation_type != operation
                or existing_mutation.target_id != quest.id
                or existing_mutation.payload_hash != payload_hash
                or existing_mutation.result_id != quest.id
            ):
                raise QuestMutationConflictError
            return QuestResult(quest, occurrence, campaign)
        result = QuestResult(quest, occurrence, campaign)
        if quest.record_version != request.record_version:
            raise StaleQuestVersionError(result)

        now = datetime.now(UTC)
        mutation = ClientMutation(
            id=uuid4(),
            user_id=user.id,
            client_mutation_id=request.client_mutation_id,
            operation_type=operation,
            payload_hash=payload_hash,
            target_type="quest",
            target_id=quest.id,
            processing_status="succeeded",
            result_type="quest",
            result_id=quest.id,
            processed_at=now,
            updated_at=now,
        )
        database_session.add(mutation)
        expected_state = "archived" if restore else "active"
        if quest.definition_state == expected_state:
            previous_campaign_state = campaign.campaign_state
            if restore:
                next_display_order = database_session.scalar(
                    select(func.coalesce(func.max(Quest.display_order) + 1, 0)).where(
                        Quest.user_id == user.id,
                        Quest.campaign_id == campaign.id,
                        Quest.definition_state == "active",
                        Quest.deleted_at.is_(None),
                        Quest.id != quest.id,
                    )
                )
                quest.display_order = int(next_display_order or 0)
            quest.definition_state = "active" if restore else "archived"
            if restore:
                quest.restored_at = now
            else:
                quest.archived_at = now
            quest.record_version += 1
            quest.updated_at = now
            campaign.record_version += 1
            campaign.updated_at = now
            database_session.flush()
            derived_state = _derived_campaign_state(database_session, campaign, now)
            campaign.campaign_state = derived_state
            if derived_state == "completed" and previous_campaign_state != "completed":
                campaign.completed_at = now
                campaign.completion_reason = "quest_obligations_satisfied"
            event_sequence = user.next_event_sequence
            user.next_event_sequence += 1
            database_session.add(
                ProgressEvent(
                    id=uuid4(),
                    user_id=user.id,
                    event_sequence=event_sequence,
                    event_type="quest_restored" if restore else "quest_archived",
                    source_type="client_mutation",
                    source_id=mutation.id,
                    client_mutation_id=request.client_mutation_id,
                    server_received_at=now,
                    server_processed_at=now,
                    rule_version=1,
                    event_metadata={
                        "campaign_id": str(campaign.id),
                        "quest_id": str(quest.id),
                    },
                )
            )
            if previous_campaign_state != derived_state:
                campaign_sequence = user.next_event_sequence
                user.next_event_sequence += 1
                database_session.add(
                    ProgressEvent(
                        id=uuid4(),
                        user_id=user.id,
                        event_sequence=campaign_sequence,
                        event_type=(
                            "campaign_completed"
                            if derived_state == "completed"
                            else "campaign_reopened"
                        ),
                        source_type="client_mutation",
                        source_id=mutation.id,
                        client_mutation_id=request.client_mutation_id,
                        server_received_at=now,
                        server_processed_at=now,
                        rule_version=1,
                        event_metadata={
                            "campaign_id": str(campaign.id),
                            "quest_id": str(quest.id),
                            "previous_state": previous_campaign_state,
                        },
                    )
                )
            user.updated_at = now
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return result

    def archive_one_time(
        self,
        database_session: Session,
        current_user: User,
        quest_id: UUID,
        request: QuestTransitionRequest,
    ) -> QuestResult:
        return self._transition_one_time(
            database_session,
            current_user,
            quest_id,
            request,
            restore=False,
        )

    def restore_one_time(
        self,
        database_session: Session,
        current_user: User,
        quest_id: UUID,
        request: QuestTransitionRequest,
    ) -> QuestResult:
        return self._transition_one_time(
            database_session,
            current_user,
            quest_id,
            request,
            restore=True,
        )

    def get_detail(
        self,
        database_session: Session,
        current_user: User,
        quest_id: UUID,
    ) -> QuestResult:
        quest = database_session.scalar(
            select(Quest).where(
                Quest.id == quest_id,
                Quest.user_id == current_user.id,
                Quest.quest_type == "one_time",
                Quest.deleted_at.is_(None),
            )
        )
        if quest is None:
            raise QuestNotFoundError
        campaign = database_session.scalar(
            select(Campaign).where(
                Campaign.id == quest.campaign_id,
                Campaign.user_id == current_user.id,
                Campaign.deleted_at.is_(None),
            )
        )
        occurrence = database_session.scalar(
            select(QuestOccurrence).where(
                QuestOccurrence.quest_id == quest.id,
                QuestOccurrence.user_id == current_user.id,
            )
        )
        if campaign is None or occurrence is None:
            raise QuestNotFoundError
        return QuestResult(quest, occurrence, campaign)

    def update_one_time(
        self,
        database_session: Session,
        current_user: User,
        quest_id: UUID,
        request: UpdateOneTimeQuestRequest,
    ) -> QuestResult:
        user = database_session.scalar(
            select(User).where(User.id == current_user.id).with_for_update()
        )
        if user is None:
            raise RuntimeError("Authenticated user record is missing.")
        quest = database_session.scalar(
            select(Quest)
            .where(
                Quest.id == quest_id,
                Quest.user_id == user.id,
                Quest.quest_type == "one_time",
                Quest.definition_state == "active",
                Quest.deleted_at.is_(None),
            )
            .with_for_update()
        )
        if quest is None:
            raise QuestNotFoundError
        campaign = database_session.scalar(
            select(Campaign).where(
                Campaign.id == quest.campaign_id,
                Campaign.user_id == user.id,
                Campaign.deleted_at.is_(None),
            )
        )
        occurrence = database_session.scalar(
            select(QuestOccurrence).where(
                QuestOccurrence.quest_id == quest.id,
                QuestOccurrence.user_id == user.id,
            )
        )
        if campaign is None or occurrence is None:
            raise QuestNotFoundError
        if campaign.campaign_state == "archived":
            raise QuestNotFoundError
        fields = request.model_fields_set - {"record_version", "client_mutation_id"}
        payload_hash = _payload_hash(
            {
                "quest_id": str(quest.id),
                "record_version": request.record_version,
                "category": request.category if "category" in fields else "<omitted>",
                "description": request.description if "description" in fields else "<omitted>",
                "difficulty": request.difficulty if "difficulty" in fields else "<omitted>",
                "reward_xp": request.reward_xp if "reward_xp" in fields else "<omitted>",
                "title": request.title if "title" in fields else "<omitted>",
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
                existing_mutation.operation_type != "one_time_quest_update"
                or existing_mutation.target_id != quest.id
                or existing_mutation.payload_hash != payload_hash
                or existing_mutation.result_id != quest.id
            ):
                raise QuestMutationConflictError
            return QuestResult(quest, occurrence, campaign)
        result = QuestResult(quest, occurrence, campaign)
        if quest.record_version != request.record_version:
            raise StaleQuestVersionError(result)
        if (
            "reward_xp" in fields
            and quest.reward_xp != request.reward_xp
            and request.reward_xp not in ALLOWED_QUEST_REWARD_XP
        ):
            raise InvalidQuestRewardError

        changed = False
        if "title" in fields and quest.title != request.title:
            quest.title = request.title or quest.title
            changed = True
        if "description" in fields and quest.description != request.description:
            quest.description = request.description
            changed = True
        if "category" in fields and quest.category != request.category:
            quest.category = request.category
            changed = True
        if "difficulty" in fields and quest.difficulty != request.difficulty:
            quest.difficulty = request.difficulty
            changed = True
        if "reward_xp" in fields and quest.reward_xp != request.reward_xp:
            quest.reward_xp = request.reward_xp if request.reward_xp is not None else quest.reward_xp
            changed = True
        now = datetime.now(UTC)
        if changed:
            quest.record_version += 1
            quest.updated_at = now
        database_session.add(
            ClientMutation(
                id=uuid4(),
                user_id=user.id,
                client_mutation_id=request.client_mutation_id,
                operation_type="one_time_quest_update",
                payload_hash=payload_hash,
                target_type="quest",
                target_id=quest.id,
                processing_status="succeeded",
                result_type="quest",
                result_id=quest.id,
                processed_at=now,
                updated_at=now,
            )
        )
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return result

    def create_one_time(
        self,
        database_session: Session,
        current_user: User,
        campaign_id: UUID,
        request: CreateOneTimeQuestRequest,
    ) -> QuestResult:
        user = database_session.scalar(
            select(User).where(User.id == current_user.id).with_for_update()
        )
        if user is None:
            raise RuntimeError("Authenticated user record is missing.")
        campaign = database_session.scalar(
            select(Campaign)
            .where(
                Campaign.id == campaign_id,
                Campaign.user_id == user.id,
                Campaign.deleted_at.is_(None),
            )
            .with_for_update()
        )
        if campaign is None:
            raise CampaignUnavailableError

        payload_hash = _payload_hash(
            {
                "campaign_id": str(campaign_id),
                "campaign_record_version": request.campaign_record_version,
                "category": request.category,
                "description": request.description,
                "difficulty": request.difficulty,
                "due_local_datetime": request.due_local_datetime,
                "reward_xp": request.reward_xp,
                "timezone_name": request.timezone_name,
                "title": request.title,
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
                existing_mutation.operation_type != "one_time_quest_create"
                or existing_mutation.target_id != campaign.id
                or existing_mutation.payload_hash != payload_hash
                or existing_mutation.result_id is None
            ):
                raise QuestMutationConflictError
            quest = database_session.scalar(
                select(Quest).where(
                    Quest.id == existing_mutation.result_id,
                    Quest.user_id == user.id,
                    Quest.campaign_id == campaign.id,
                )
            )
            occurrence = database_session.scalar(
                select(QuestOccurrence).where(
                    QuestOccurrence.quest_id == existing_mutation.result_id,
                    QuestOccurrence.user_id == user.id,
                )
            )
            if quest is None or occurrence is None:
                raise RuntimeError("Quest mutation result is incomplete.")
            return QuestResult(quest, occurrence, campaign)
        if campaign.campaign_state != "active":
            raise CampaignUnavailableError
        if campaign.record_version != request.campaign_record_version:
            raise StaleCampaignVersionError(campaign)

        preference = database_session.get(UserPreference, user.id)
        if preference is None:
            raise RuntimeError("Active user preference record is missing.")
        timezone_name = request.timezone_name or preference.timezone_name
        try:
            validate_timezone_name(timezone_name)
            timezone = ZoneInfo(timezone_name)
        except (InvalidTimezoneError, ValueError, ZoneInfoNotFoundError) as error:
            raise InvalidQuestScheduleError from error
        now = datetime.now(UTC)
        due_at = (
            _resolve_local_due(request.due_local_datetime, timezone)
            if request.due_local_datetime is not None
            else None
        )
        if due_at is not None and due_at <= now:
            raise InvalidQuestScheduleError
        quest_id = uuid4()
        display_order = database_session.scalar(
            select(func.coalesce(func.max(Quest.display_order) + 1, 0)).where(
                Quest.user_id == user.id,
                Quest.campaign_id == campaign.id,
                Quest.definition_state == "active",
                Quest.deleted_at.is_(None),
            )
        )
        quest = Quest(
            id=quest_id,
            user_id=user.id,
            campaign_id=campaign.id,
            quest_type="one_time",
            title=request.title,
            description=request.description,
            category=request.category,
            difficulty=request.difficulty,
            reward_xp=request.reward_xp,
            display_order=int(display_order or 0),
            due_at=due_at,
            one_time_timezone_name=timezone_name if due_at is not None else None,
        )
        occurrence = QuestOccurrence(
            id=uuid4(),
            user_id=user.id,
            campaign_id=campaign.id,
            quest_id=quest_id,
            quest_type="one_time",
            occurrence_state="available",
            occurrence_local_date=now.astimezone(timezone).date(),
            timezone_name=timezone_name,
            timezone_data_version=_timezone_data_version(),
            rule_version=1,
            available_at=now,
            eligibility_expires_at=due_at,
            reward_xp=request.reward_xp,
        )
        mutation = ClientMutation(
            id=uuid4(),
            user_id=user.id,
            client_mutation_id=request.client_mutation_id,
            operation_type="one_time_quest_create",
            payload_hash=payload_hash,
            target_type="campaign",
            target_id=campaign.id,
            processing_status="succeeded",
            result_type="quest",
            result_id=quest.id,
            processed_at=now,
            updated_at=now,
        )
        campaign.record_version += 1
        campaign.updated_at = now
        database_session.add_all([quest, occurrence, mutation])
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return QuestResult(quest, occurrence, campaign)
