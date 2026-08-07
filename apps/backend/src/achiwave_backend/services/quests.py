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
    User,
    UserPreference,
)
from achiwave_backend.schemas.quests import CreateOneTimeQuestRequest


class CampaignUnavailableError(Exception):
    """The owner-visible campaign cannot accept a new quest."""


class QuestMutationConflictError(Exception):
    """A mutation identifier is already bound to another payload."""


class StaleCampaignVersionError(Exception):
    def __init__(self, campaign: Campaign) -> None:
        self.campaign = campaign


class QuestCreateResult:
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
    def create_one_time(
        self,
        database_session: Session,
        current_user: User,
        campaign_id: UUID,
        request: CreateOneTimeQuestRequest,
    ) -> QuestCreateResult:
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
            return QuestCreateResult(quest, occurrence, campaign)
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
        return QuestCreateResult(quest, occurrence, campaign)
