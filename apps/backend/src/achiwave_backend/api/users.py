from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import AuthenticationDependencies
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.models import User
from achiwave_backend.schemas.users import (
    CurrentUserResponse,
    UpdateCurrentUserRequest,
)
from achiwave_backend.services.profile import ProfileService, StaleProfileVersionError


def _current_user_response(user: User) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=user.id,
        email=user.display_email,
        display_name=user.display_name,
        account_state="active",
        record_version=user.record_version,
    )


def create_users_router(
    authentication: AuthenticationDependencies,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/users", tags=["users"])
    service = ProfileService()

    @router.get("/me", response_model=CurrentUserResponse)
    def current_user(
        user: User = Depends(authentication.current_user),
    ) -> CurrentUserResponse:
        return _current_user_response(user)

    @router.patch(
        "/me",
        response_model=CurrentUserResponse,
        responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
    )
    def update_current_user(
        request: UpdateCurrentUserRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> CurrentUserResponse:
        try:
            updated = service.update_current(database_session, user, request)
        except StaleProfileVersionError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message="The profile changed before this update was applied.",
            ) from error
        return _current_user_response(updated)

    return router
