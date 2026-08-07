import hashlib
import json
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from achiwave_backend.models import (
    Campaign,
    ClientMutation,
    Quest,
    QuestOccurrence,
    ProgressEvent,
    User,
)
from achiwave_backend.schemas.campaigns import (
    CampaignTransitionRequest,
    CreateCampaignRequest,
    UpdateCampaignRequest,
)


class ClientMutationConflictError(Exception):
    """A mutation identifier was already bound to another canonical payload."""


class CampaignListResult:
    def __init__(
        self,
        *,
        items: list[tuple[Campaign, int, int]],
        total: int,
        limit: int,
        offset: int,
    ) -> None:
        self.items = items
        self.total = total
        self.limit = limit
        self.offset = offset


class CampaignNotFoundError(Exception):
    """No owner-visible campaign matches the supplied identifier."""


class StaleCampaignVersionError(Exception):
    def __init__(self, campaign: Campaign) -> None:
        self.campaign = campaign


class CampaignDetailResult:
    def __init__(
        self,
        campaign: Campaign,
        quests: list[tuple[Quest, str]],
        *,
        include_archived_quests: bool,
    ) -> None:
        self.campaign = campaign
        self.quests = quests
        self.visible_quests = (
            quests
            if include_archived_quests
            else [row for row in quests if row[0].definition_state == "active"]
        )


def _payload_hash(payload: dict[str, object]) -> bytes:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).digest()


def _commit(database_session: Session) -> None:
    try:
        database_session.commit()
    except Exception:
        database_session.rollback()
        raise


class CampaignService:
    def archive(
        self,
        database_session: Session,
        current_user: User,
        campaign_id: UUID,
        request: CampaignTransitionRequest,
    ) -> Campaign:
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
            raise CampaignNotFoundError
        payload_hash = _payload_hash(
            {
                "campaign_id": str(campaign.id),
                "record_version": request.record_version,
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
                existing_mutation.operation_type != "campaign_archive"
                or existing_mutation.target_id != campaign.id
                or existing_mutation.payload_hash != payload_hash
                or existing_mutation.result_id != campaign.id
            ):
                raise ClientMutationConflictError
            return campaign
        if campaign.record_version != request.record_version:
            raise StaleCampaignVersionError(campaign)

        now = datetime.now(UTC)
        mutation = ClientMutation(
            id=uuid4(),
            user_id=user.id,
            client_mutation_id=request.client_mutation_id,
            operation_type="campaign_archive",
            payload_hash=payload_hash,
            target_type="campaign",
            target_id=campaign.id,
            processing_status="succeeded",
            result_type="campaign",
            result_id=campaign.id,
            processed_at=now,
            updated_at=now,
        )
        database_session.add(mutation)
        if campaign.campaign_state != "archived":
            previous_state = campaign.campaign_state
            campaign.campaign_state = "archived"
            campaign.archived_at = now
            campaign.record_version += 1
            campaign.updated_at = now
            event_sequence = user.next_event_sequence
            user.next_event_sequence += 1
            user.updated_at = now
            database_session.add(
                ProgressEvent(
                    id=uuid4(),
                    user_id=user.id,
                    event_sequence=event_sequence,
                    event_type="campaign_archived",
                    source_type="client_mutation",
                    source_id=mutation.id,
                    client_mutation_id=request.client_mutation_id,
                    server_received_at=now,
                    server_processed_at=now,
                    rule_version=1,
                    event_metadata={
                        "campaign_id": str(campaign.id),
                        "previous_state": previous_state,
                    },
                )
            )
        _commit(database_session)
        return campaign

    def update(
        self,
        database_session: Session,
        current_user: User,
        campaign_id: UUID,
        request: UpdateCampaignRequest,
    ) -> Campaign:
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
            raise CampaignNotFoundError
        fields = request.model_fields_set - {"record_version", "client_mutation_id"}
        payload_hash = _payload_hash(
            {
                "campaign_id": str(campaign_id),
                "description": request.description if "description" in fields else "<omitted>",
                "record_version": request.record_version,
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
                existing_mutation.operation_type != "campaign_update"
                or existing_mutation.target_id != campaign.id
                or existing_mutation.payload_hash != payload_hash
                or existing_mutation.result_id != campaign.id
            ):
                raise ClientMutationConflictError
            return campaign
        if campaign.record_version != request.record_version:
            raise StaleCampaignVersionError(campaign)

        changed = False
        if "title" in fields and campaign.title != request.title:
            campaign.title = request.title or campaign.title
            changed = True
        if "description" in fields and campaign.description != request.description:
            campaign.description = request.description
            changed = True
        now = datetime.now(UTC)
        if changed:
            campaign.record_version += 1
            campaign.updated_at = now
        database_session.add(
            ClientMutation(
                id=uuid4(),
                user_id=user.id,
                client_mutation_id=request.client_mutation_id,
                operation_type="campaign_update",
                payload_hash=payload_hash,
                target_type="campaign",
                target_id=campaign.id,
                processing_status="succeeded",
                result_type="campaign",
                result_id=campaign.id,
                processed_at=now,
                updated_at=now,
            )
        )
        _commit(database_session)
        return campaign

    def get_detail(
        self,
        database_session: Session,
        current_user: User,
        campaign_id: UUID,
        *,
        include_archived_quests: bool,
    ) -> CampaignDetailResult:
        campaign = database_session.scalar(
            select(Campaign).where(
                Campaign.id == campaign_id,
                Campaign.user_id == current_user.id,
                Campaign.deleted_at.is_(None),
            )
        )
        if campaign is None:
            raise CampaignNotFoundError
        occurrence_state = (
            select(QuestOccurrence.occurrence_state)
            .where(
                QuestOccurrence.quest_id == Quest.id,
                QuestOccurrence.user_id == current_user.id,
            )
            .order_by(QuestOccurrence.generated_at.desc(), QuestOccurrence.id)
            .limit(1)
            .correlate(Quest)
            .scalar_subquery()
        )
        product_status = case(
            (Quest.definition_state == "archived", "archived"),
            (Quest.quest_type == "recurring", "active"),
            else_=func.coalesce(occurrence_state, "active"),
        )
        quests = [
            (quest, str(status))
            for quest, status in database_session.execute(
                select(Quest, product_status)
                .where(
                    Quest.campaign_id == campaign.id,
                    Quest.user_id == current_user.id,
                    Quest.deleted_at.is_(None),
                )
                .order_by(Quest.display_order, Quest.id)
            )
        ]
        return CampaignDetailResult(
            campaign,
            quests,
            include_archived_quests=include_archived_quests,
        )

    def list(
        self,
        database_session: Session,
        current_user: User,
        *,
        view: str,
        limit: int,
        offset: int,
    ) -> CampaignListResult:
        state_filter = (
            Campaign.campaign_state == "archived"
            if view == "archived"
            else Campaign.campaign_state.in_(("active", "completed"))
        )
        filters = (
            Campaign.user_id == current_user.id,
            Campaign.deleted_at.is_(None),
            state_filter,
        )
        active_quests = (
            select(func.count())
            .select_from(Quest)
            .where(
                Quest.user_id == current_user.id,
                Quest.campaign_id == Campaign.id,
                Quest.definition_state == "active",
                Quest.deleted_at.is_(None),
            )
            .correlate(Campaign)
            .scalar_subquery()
        )
        archived_quests = (
            select(func.count())
            .select_from(Quest)
            .where(
                Quest.user_id == current_user.id,
                Quest.campaign_id == Campaign.id,
                Quest.definition_state == "archived",
                Quest.deleted_at.is_(None),
            )
            .correlate(Campaign)
            .scalar_subquery()
        )
        ordering = (
            (Campaign.archived_at.desc(), Campaign.id)
            if view == "archived"
            else (Campaign.display_order, Campaign.id)
        )
        rows = database_session.execute(
            select(Campaign, active_quests, archived_quests)
            .where(*filters)
            .order_by(*ordering)
            .limit(limit)
            .offset(offset)
        ).all()
        total = database_session.scalar(
            select(func.count()).select_from(Campaign).where(*filters)
        )
        return CampaignListResult(
            items=[
                (campaign, int(active_count), int(archived_count))
                for campaign, active_count, archived_count in rows
            ],
            total=int(total or 0),
            limit=limit,
            offset=offset,
        )

    def create(
        self,
        database_session: Session,
        current_user: User,
        request: CreateCampaignRequest,
    ) -> Campaign:
        user = database_session.scalar(
            select(User).where(User.id == current_user.id).with_for_update()
        )
        if user is None:
            raise RuntimeError("Authenticated user record is missing.")

        payload_hash = _payload_hash(
            {
                "description": request.description,
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
                existing_mutation.operation_type != "campaign_create"
                or existing_mutation.payload_hash != payload_hash
                or existing_mutation.result_id is None
            ):
                raise ClientMutationConflictError
            campaign = database_session.scalar(
                select(Campaign).where(
                    Campaign.id == existing_mutation.result_id,
                    Campaign.user_id == user.id,
                )
            )
            if campaign is None:
                raise RuntimeError("Campaign mutation result is missing.")
            return campaign

        campaign_id = uuid4()
        display_order = database_session.scalar(
            select(func.coalesce(func.max(Campaign.display_order) + 1, 0)).where(
                Campaign.user_id == user.id,
                Campaign.deleted_at.is_(None),
            )
        )
        campaign = Campaign(
            id=campaign_id,
            user_id=user.id,
            title=request.title,
            description=request.description,
            display_order=int(display_order or 0),
            campaign_state="active",
            record_version=1,
        )
        now = datetime.now(UTC)
        mutation = ClientMutation(
            id=uuid4(),
            user_id=user.id,
            client_mutation_id=request.client_mutation_id,
            operation_type="campaign_create",
            payload_hash=payload_hash,
            target_type="campaign",
            target_id=campaign_id,
            processing_status="succeeded",
            result_type="campaign",
            result_id=campaign_id,
            processed_at=now,
            updated_at=now,
        )
        database_session.add_all([mutation, campaign])
        _commit(database_session)
        return campaign
