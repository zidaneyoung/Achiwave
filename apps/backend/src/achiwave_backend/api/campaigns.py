from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import AuthenticationDependencies
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.models import Campaign, User
from achiwave_backend.schemas.campaigns import (
    CampaignListItemResponse,
    CampaignListResponse,
    CampaignQuestSummaryResponse,
    CampaignResponse,
    CreateCampaignRequest,
)
from achiwave_backend.services.campaigns import (
    CampaignService,
    ClientMutationConflictError,
)


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
