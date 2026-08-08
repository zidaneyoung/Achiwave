from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import AuthenticationDependencies
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.models import Campaign, User
from achiwave_backend.quest_configuration import quest_category_label

from achiwave_backend.schemas.campaigns import (
    CampaignDetailResponse,
    CampaignConflictResponse,
    CampaignQuestResponse,
    CampaignListItemResponse,
    CampaignListResponse,
    CampaignQuestSummaryResponse,
    CampaignResponse,
    CampaignTransitionRequest,
    CreateCampaignRequest,
    UpdateCampaignRequest,
)
from achiwave_backend.services.campaigns import (
    CampaignNotFoundError,
    CampaignService,
    ClientMutationConflictError,
    InvalidCampaignStructureError,
    StaleCampaignVersionError,
)
from achiwave_backend.services.quests import quest_due_status


def campaign_response(campaign: Campaign) -> CampaignResponse:
    return CampaignResponse(
        id=campaign.id,
        title=campaign.title,
        description=campaign.description,
        display_order=campaign.display_order,
        status=campaign.campaign_state,
        record_version=campaign.record_version,
        completed_at=campaign.completed_at,
        archived_at=campaign.archived_at,
        restored_at=campaign.restored_at,
        created_at=campaign.created_at,
        updated_at=campaign.updated_at,
    )


def create_campaigns_router(
    authentication: AuthenticationDependencies,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])
    service = CampaignService()

    @router.post(
        "/{campaign_id}/restore",
        response_model=CampaignResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": CampaignConflictResponse},
        },
    )
    def restore_campaign(
        campaign_id: UUID,
        request: CampaignTransitionRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> CampaignResponse:
        try:
            campaign = service.restore(database_session, user, campaign_id, request)
        except CampaignNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="campaign_not_found",
                message="The campaign was not found.",
            ) from error
        except InvalidCampaignStructureError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="campaign_restore_invalid",
                message="The campaign has invalid quest data and cannot be restored.",
            ) from error
        except StaleCampaignVersionError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message="The campaign changed before restoration was applied.",
                details={
                    "current": campaign_response(error.campaign).model_dump(mode="json")
                },
            ) from error
        except ClientMutationConflictError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="client_mutation_conflict",
                message="This request identifier was already used for another action.",
            ) from error
        return campaign_response(campaign)

    @router.post(
        "/{campaign_id}/archive",
        response_model=CampaignResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": CampaignConflictResponse},
        },
    )
    def archive_campaign(
        campaign_id: UUID,
        request: CampaignTransitionRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> CampaignResponse:
        try:
            campaign = service.archive(database_session, user, campaign_id, request)
        except CampaignNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="campaign_not_found",
                message="The campaign was not found.",
            ) from error
        except StaleCampaignVersionError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message="The campaign changed before archival was applied.",
                details={
                    "current": campaign_response(error.campaign).model_dump(mode="json")
                },
            ) from error
        except ClientMutationConflictError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="client_mutation_conflict",
                message="This request identifier was already used for another action.",
            ) from error
        return campaign_response(campaign)

    @router.patch(
        "/{campaign_id}",
        response_model=CampaignResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": CampaignConflictResponse},
        },
    )
    def update_campaign(
        campaign_id: UUID,
        request: UpdateCampaignRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> CampaignResponse:
        try:
            campaign = service.update(database_session, user, campaign_id, request)
        except CampaignNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="campaign_not_found",
                message="The campaign was not found.",
            ) from error
        except StaleCampaignVersionError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message="The campaign changed before this update was applied.",
                details={
                    "current": campaign_response(error.campaign).model_dump(mode="json")
                },
            ) from error
        except ClientMutationConflictError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="client_mutation_conflict",
                message="This request identifier was already used for another action.",
            ) from error
        return campaign_response(campaign)

    @router.get(
        "/{campaign_id}",
        response_model=CampaignDetailResponse,
        responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
    )
    def get_campaign(
        campaign_id: UUID,
        include_archived_quests: bool = False,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> CampaignDetailResponse:
        try:
            result = service.get_detail(
                database_session,
                user,
                campaign_id,
                include_archived_quests=include_archived_quests,
            )
        except CampaignNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="campaign_not_found",
                message="The campaign was not found.",
            ) from error
        active_count = sum(
            quest.definition_state == "active" for quest, _ in result.quests
        )
        archived_count = sum(
            quest.definition_state == "archived" for quest, _ in result.quests
        )
        return CampaignDetailResponse(
            **campaign_response(result.campaign).model_dump(),
            quest_summary=CampaignQuestSummaryResponse(
                active=active_count,
                archived=archived_count,
                total=active_count + archived_count,
            ),
            quests=[
                CampaignQuestResponse(
                    id=quest.id,
                    campaign_id=quest.campaign_id,
                    quest_type=quest.quest_type,
                    definition_state=quest.definition_state,
                    status=quest_status,
                    title=quest.title,
                    description=quest.description,
                    category=quest.category,
                    category_label=quest_category_label(quest.category),
                    reward_xp=quest.reward_xp,
                    display_order=quest.display_order,
                    available_from=quest.available_from,
                    due_at=quest.due_at,
                    timezone_name=quest.one_time_timezone_name,
                    due_status=quest_due_status(
                        quest,
                        quest_status,
                        result.campaign.campaign_state,
                    ),
                    record_version=quest.record_version,
                    archived_at=quest.archived_at,
                    restored_at=quest.restored_at,
                    created_at=quest.created_at,
                    updated_at=quest.updated_at,
                )
                for quest, quest_status in result.visible_quests
            ],
        )

    @router.get("", response_model=CampaignListResponse)
    def list_campaigns(
        view: Literal["active", "archived"] = "active",
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> CampaignListResponse:
        result = service.list(
            database_session,
            user,
            view=view,
            limit=limit,
            offset=offset,
        )
        return CampaignListResponse(
            items=[
                CampaignListItemResponse(
                    **campaign_response(campaign).model_dump(),
                    quest_summary=CampaignQuestSummaryResponse(
                        active=active_count,
                        archived=archived_count,
                        total=active_count + archived_count,
                    ),
                )
                for campaign, active_count, archived_count in result.items
            ],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    @router.post(
        "",
        response_model=CampaignResponse,
        status_code=status.HTTP_201_CREATED,
        responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
    )
    def create_campaign(
        request: CreateCampaignRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> CampaignResponse:
        try:
            campaign = service.create(database_session, user, request)
        except ClientMutationConflictError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="client_mutation_conflict",
                message="This request identifier was already used for another action.",
            ) from error
        return campaign_response(campaign)

    return router
