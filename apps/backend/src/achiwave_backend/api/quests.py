from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from achiwave_backend.api.campaigns import campaign_response
from achiwave_backend.api.dependencies import AuthenticationDependencies
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.models import User
from achiwave_backend.quest_configuration import (
    QUEST_CATEGORY_LABELS,
    QUEST_DIFFICULTY_LABELS,
    ALLOWED_QUEST_REWARD_XP,
)
from achiwave_backend.schemas.campaigns import CampaignConflictResponse
from achiwave_backend.schemas.quests import (
    CreateOneTimeQuestRequest,
    QuestAuthoringOptionResponse,
    QuestAuthoringOptionsResponse,
    QuestConflictResponse,
    QuestListCategory,
    QuestListItemResponse,
    QuestListResponse,
    QuestListStatus,
    QuestOrderConflictResponse,
    QuestOrderItemResponse,
    QuestOrderResponse,
    QuestResponse,
    QuestTransitionRequest,
    ReorderActiveQuestsRequest,
    UpdateOneTimeQuestRequest,
)
from achiwave_backend.services.quests import (
    CampaignUnavailableError,
    InvalidQuestRewardError,
    InvalidQuestOrderError,
    InvalidQuestScheduleError,
    QuestMutationConflictError,
    QuestNotFoundError,
    QuestResult,
    QuestOrderResult,
    QuestService,
    StaleCampaignVersionError,
    StaleQuestVersionError,
    StaleQuestOrderError,
    quest_response,
)


def quest_order_response(result: QuestOrderResult) -> QuestOrderResponse:
    return QuestOrderResponse(
        campaign_id=result.campaign_id,
        campaign_record_version=result.campaign_record_version,
        items=[
            QuestOrderItemResponse(
                id=item.id,
                display_order=item.display_order,
                record_version=item.record_version,
            )
            for item in result.items
        ],
    )


def create_quests_router(
    authentication: AuthenticationDependencies,
) -> APIRouter:
    router = APIRouter(tags=["quests"])
    service = QuestService()

    @router.get(
        "/api/v1/quests/authoring-options",
        response_model=QuestAuthoringOptionsResponse,
    )
    def get_quest_authoring_options(
        _user: User = Depends(authentication.current_user),
    ) -> QuestAuthoringOptionsResponse:
        return QuestAuthoringOptionsResponse(
            categories=[
                QuestAuthoringOptionResponse(value=value, label=label)
                for value, label in QUEST_CATEGORY_LABELS.items()
            ],
            difficulties=[
                QuestAuthoringOptionResponse(value=value, label=label)
                for value, label in QUEST_DIFFICULTY_LABELS.items()
            ],
            reward_xp_values=list(ALLOWED_QUEST_REWARD_XP),
        )

    @router.get(
        "/api/v1/quests",
        response_model=QuestListResponse,
        responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse}},
    )
    def list_quests(
        campaign_id: UUID | None = None,
        quest_status: QuestListStatus | None = Query(default=None, alias="status"),
        category: QuestListCategory | None = None,
        due_from: date | None = None,
        due_to: date | None = None,
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> QuestListResponse:
        if due_from is not None and due_to is not None and due_from > due_to:
            raise ApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="invalid_due_date_range",
                message="The due-date start must not be after the end.",
            )
        result = service.list(
            database_session,
            user,
            campaign_id=campaign_id,
            quest_status=quest_status,
            category=category,
            due_from=due_from,
            due_to=due_to,
            limit=limit,
            offset=offset,
        )
        return QuestListResponse(
            items=[
                QuestListItemResponse(
                    **quest_response(
                        QuestResult(item.quest, item.occurrence, item.campaign)
                    ).model_dump(),
                    campaign_title=item.campaign.title,
                    status=item.status,
                )
                for item in result.items
            ],
            total=result.total,
            limit=result.limit,
            offset=result.offset,
        )

    @router.put(
        "/api/v1/campaigns/{campaign_id}/quests/order",
        response_model=QuestOrderResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": QuestOrderConflictResponse},
            status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        },
    )
    def reorder_active_quests(
        campaign_id: UUID,
        request: ReorderActiveQuestsRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> QuestOrderResponse:
        try:
            result = service.reorder_active(
                database_session,
                user,
                campaign_id,
                request,
            )
        except CampaignUnavailableError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="campaign_not_found",
                message="The campaign is unavailable for quest reordering.",
            ) from error
        except InvalidQuestOrderError as error:
            raise ApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="invalid_quest_order",
                message="Submit every active quest exactly once.",
            ) from error
        except StaleQuestOrderError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message="Campaign or quest order changed before this request was applied.",
                details={
                    "current": quest_order_response(error.result).model_dump(mode="json")
                },
            ) from error
        except QuestMutationConflictError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="client_mutation_conflict",
                message="This request identifier was already used for another action.",
            ) from error
        return quest_order_response(result)

    def transition_error(error: Exception, *, action: str) -> ApiError:
        if isinstance(error, QuestNotFoundError):
            return ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="quest_not_found",
                message="The quest was not found.",
            )
        if isinstance(error, StaleQuestVersionError):
            return ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message=f"The quest changed before {action} was applied.",
                details={"current": quest_response(error.result).model_dump(mode="json")},
            )
        return ApiError(
            status_code=status.HTTP_409_CONFLICT,
            code="client_mutation_conflict",
            message="This request identifier was already used for another action.",
        )

    @router.post(
        "/api/v1/quests/{quest_id}/restore",
        response_model=QuestResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": QuestConflictResponse},
        },
    )
    def restore_one_time_quest(
        quest_id: UUID,
        request: QuestTransitionRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> QuestResponse:
        try:
            result = service.restore_one_time(database_session, user, quest_id, request)
        except (QuestNotFoundError, StaleQuestVersionError, QuestMutationConflictError) as error:
            raise transition_error(error, action="restoration") from error
        return result

    @router.post(
        "/api/v1/quests/{quest_id}/archive",
        response_model=QuestResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": QuestConflictResponse},
        },
    )
    def archive_one_time_quest(
        quest_id: UUID,
        request: QuestTransitionRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> QuestResponse:
        try:
            result = service.archive_one_time(database_session, user, quest_id, request)
        except (QuestNotFoundError, StaleQuestVersionError, QuestMutationConflictError) as error:
            raise transition_error(error, action="archival") from error
        return result

    @router.patch(
        "/api/v1/quests/{quest_id}",
        response_model=QuestResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": QuestConflictResponse},
        },
    )
    def update_one_time_quest(
        quest_id: UUID,
        request: UpdateOneTimeQuestRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> QuestResponse:
        try:
            result = service.update_one_time(database_session, user, quest_id, request)
        except QuestNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="quest_not_found",
                message="The quest was not found.",
            ) from error
        except StaleQuestVersionError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message="The quest changed before this update was applied.",
                details={"current": quest_response(error.result).model_dump(mode="json")},
            ) from error
        except QuestMutationConflictError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="client_mutation_conflict",
                message="This request identifier was already used for another action.",
            ) from error
        except InvalidQuestRewardError as error:
            raise ApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="invalid_reward_xp",
                message="Choose an allowed quest XP reward.",
            ) from error
        return quest_response(result)

    @router.get(
        "/api/v1/quests/{quest_id}",
        response_model=QuestResponse,
        responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
    )
    def get_one_time_quest(
        quest_id: UUID,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> QuestResponse:
        try:
            result = service.get_detail(database_session, user, quest_id)
        except QuestNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="quest_not_found",
                message="The quest was not found.",
            ) from error
        return quest_response(result)

    @router.post(
        "/api/v1/campaigns/{campaign_id}/quests",
        response_model=QuestResponse,
        status_code=status.HTTP_201_CREATED,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": CampaignConflictResponse},
        },
    )
    def create_one_time_quest(
        campaign_id: UUID,
        request: CreateOneTimeQuestRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> QuestResponse:
        try:
            result = service.create_one_time(
                database_session,
                user,
                campaign_id,
                request,
            )
        except CampaignUnavailableError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="campaign_not_found",
                message="The campaign is unavailable for quest creation.",
            ) from error
        except StaleCampaignVersionError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message="The campaign changed before this quest was created.",
                details={
                    "current": campaign_response(error.campaign).model_dump(mode="json")
                },
            ) from error
        except QuestMutationConflictError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="client_mutation_conflict",
                message="This request identifier was already used for another action.",
            ) from error
        except InvalidQuestScheduleError as error:
            raise ApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="invalid_due_date",
                message="The due date must resolve to a valid future instant.",
            ) from error
        return quest_response(result)

    return router
