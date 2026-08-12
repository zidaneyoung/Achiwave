from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import AuthenticationContext, AuthenticationDependencies
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.schemas.completions import (
    CompleteOccurrenceRequest,
    CompleteOccurrenceResponse,
    ReverseCompletionRequest,
    ReverseCompletionResponse,
)
from achiwave_backend.services.completions import (
    CompletionMutationConflictError,
    CompletionNotFoundError,
    CompletionRejectedError,
    CompletionService,
)


def create_completions_router(
    authentication: AuthenticationDependencies,
) -> APIRouter:
    router = APIRouter(tags=["completions"])
    service = CompletionService()

    @router.post(
        "/api/v1/quest-occurrences/{occurrence_id}/complete",
        response_model=CompleteOccurrenceResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        },
    )
    def complete_occurrence(
        occurrence_id: UUID,
        request: CompleteOccurrenceRequest,
        context: AuthenticationContext = Depends(authentication.current_context),
        database_session: Session = Depends(authentication.database_session),
    ) -> CompleteOccurrenceResponse:
        try:
            return service.complete(
                database_session,
                context.user,
                occurrence_id,
                request,
            )
        except CompletionNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="occurrence_not_found",
                message="The quest occurrence was not found.",
            ) from error
        except CompletionMutationConflictError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="client_mutation_conflict",
                message="This request identifier was already used for another action.",
            ) from error
        except CompletionRejectedError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code=error.code,
                message=error.message,
                details={"current": error.current} if error.current else None,
            ) from error

    @router.post(
        "/api/v1/quest-completions/{completion_id}/reverse",
        response_model=ReverseCompletionResponse,
        responses={
            status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        },
    )
    def reverse_completion(
        completion_id: UUID,
        request: ReverseCompletionRequest,
        context: AuthenticationContext = Depends(authentication.current_context),
        database_session: Session = Depends(authentication.database_session),
    ) -> ReverseCompletionResponse:
        try:
            return service.reverse(
                database_session,
                context.user,
                completion_id,
                request,
            )
        except CompletionNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="completion_not_found",
                message="The quest completion was not found.",
            ) from error
        except CompletionMutationConflictError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="client_mutation_conflict",
                message="This request identifier was already used for another action.",
            ) from error
        except CompletionRejectedError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code=error.code,
                message=error.message,
                details={"current": error.current} if error.current else None,
            ) from error

    return router
