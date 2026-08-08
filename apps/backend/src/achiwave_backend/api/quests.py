from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from achiwave_backend.api.campaigns import campaign_response
from achiwave_backend.api.dependencies import AuthenticationDependencies
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.models import Quest, QuestOccurrence, User
from achiwave_backend.quest_configuration import (
    QUEST_CATEGORY_LABELS,
    QUEST_DIFFICULTY_LABELS,
    ALLOWED_QUEST_REWARD_XP,
    quest_category_label,
    quest_difficulty_label,
)
from achiwave_backend.schemas.campaigns import CampaignConflictResponse
from achiwave_backend.schemas.quests import (
    CreateOneTimeQuestRequest,
    QuestAuthoringOptionResponse,
    QuestAuthoringOptionsResponse,
    QuestConflictResponse,
    QuestOccurrenceResponse,
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
    quest_due_status,
)


def _occurrence_response(occurrence: QuestOccurrence) -> QuestOccurrenceResponse:
    return QuestOccurrenceResponse(
        id=occurrence.id,
        status=occurrence.occurrence_state,
        occurrence_local_date=occurrence.occurrence_local_date,
        timezone_name=occurrence.timezone_name,
        available_at=occurrence.available_at,
        eligibility_expires_at=occurrence.eligibility_expires_at,
        reward_xp=occurrence.reward_xp,
        record_version=occurrence.record_version,
    )


def quest_response(result: QuestResult) -> QuestResponse:
    quest: Quest = result.quest
    return QuestResponse(
        id=quest.id,
        campaign_id=quest.campaign_id,
        campaign_record_version=result.campaign.record_version,
        campaign_status=result.campaign.campaign_state,
        quest_type=quest.quest_type,
        definition_state=quest.definition_state,
        title=quest.title,
        description=quest.description,
        category=quest.category,
        category_label=quest_category_label(quest.category),
        difficulty=quest.difficulty,
        difficulty_label=quest_difficulty_label(quest.difficulty),
        reward_xp=quest.reward_xp,
        display_order=quest.display_order,
        available_from=quest.available_from,
        due_at=quest.due_at,
        timezone_name=quest.one_time_timezone_name,
        due_status=quest_due_status(
            quest,
            result.occurrence.occurrence_state,
            result.campaign.campaign_state,
        ),
        record_version=quest.record_version,
        archived_at=quest.archived_at,
        restored_at=quest.restored_at,
        created_at=quest.created_at,
        updated_at=quest.updated_at,
        occurrence=_occurrence_response(result.occurrence),
    )


def quest_order_response(result: QuestOrderResult) -> QuestOrderResponse:
    return QuestOrderResponse(
        campaign_id=result.campaign.id,
        campaign_record_version=result.campaign.record_version,
        items=[
            QuestOrderItemResponse(
                id=quest.id,
                display_order=quest.display_order,
                record_version=quest.record_version,
            )
            for quest in result.quests
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
        return quest_response(result)

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
        return quest_response(result)

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
