from fastapi import APIRouter, Depends

from achiwave_backend.api.dependencies import AuthenticationDependencies
from achiwave_backend.models import User
from achiwave_backend.schemas.users import CurrentUserResponse


def create_users_router(
    authentication: AuthenticationDependencies,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/users", tags=["users"])

    @router.get("/me", response_model=CurrentUserResponse)
    def current_user(
        user: User = Depends(authentication.current_user),
    ) -> CurrentUserResponse:
        return CurrentUserResponse(
            id=user.id,
            email=user.display_email,
            account_state="active",
            record_version=user.record_version,
        )

    return router
