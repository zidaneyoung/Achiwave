import hashlib
import json
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
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
from achiwave_backend.schemas.quests import (
    CreateOneTimeQuestRequest,
    QuestTransitionRequest,
    UpdateOneTimeQuestRequest,
)
from achiwave_backend.services.campaigns import _derived_campaign_state


class CampaignUnavailableError(Exception):
    """The owner-visible campaign cannot accept a new quest."""


class QuestMutationConflictError(Exception):
    """A mutation identifier is already bound to another payload."""


class StaleCampaignVersionError(Exception):
    def __init__(self, campaign: Campaign) -> None:
        self.campaign = campaign


class QuestNotFoundError(Exception):
    """No owner-visible one-time quest matches the supplied identifier."""


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


def _payload_hash(payload: dict[str, object]) -> bytes:
    canonical = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).digest()


def _timezone_data_version() -> str:
    try:
        return f"tzdata-{version('tzdata')}"
    except PackageNotFoundError:
        return "system"


def _preference_zone(preference: UserPreference) -> tuple[str, ZoneInfo]:
    try:
        return preference.timezone_name, ZoneInfo(preference.timezone_name)
    except (ValueError, ZoneInfoNotFoundError):
        return "UTC", ZoneInfo("UTC")


class QuestService:
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
                "description": request.description if "description" in fields else "<omitted>",
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

        changed = False
        if "title" in fields and quest.title != request.title:
            quest.title = request.title or quest.title
            changed = True
        if "description" in fields and quest.description != request.description:
            quest.description = request.description
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
                "description": request.description,
                "reward_xp": request.reward_xp,
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
        timezone_name, timezone = _preference_zone(preference)
        now = datetime.now(UTC)
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
            reward_xp=request.reward_xp,
            display_order=int(display_order or 0),
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
