from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import AuthenticationContext, AuthenticationDependencies
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.auth.passwords import PasswordManager
from achiwave_backend.config import Settings
from achiwave_backend.schemas.account import (
    AccountDeactivationRequest,
    AccountDeactivationResponse,
)
from achiwave_backend.services.account import (
    AccountCannotBeDeactivatedError,
    AccountDeactivationService,
    InvalidDeactivationPasswordError,
)


def create_account_router(
    settings: Settings,
    authentication: AuthenticationDependencies,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/account", tags=["account"])
    service = AccountDeactivationService(PasswordManager(settings))

    @router.post(
        "/deactivate",
        response_model=AccountDeactivationResponse,
        responses={
            status.HTTP_401_UNAUTHORIZED: {"model": ErrorResponse},
            status.HTTP_409_CONFLICT: {"model": ErrorResponse},
        },
    )
    def deactivate_account(
        request: AccountDeactivationRequest,
        context: AuthenticationContext = Depends(authentication.current_context),
        database_session: Session = Depends(authentication.database_session),
    ) -> AccountDeactivationResponse:
        try:
            result = service.deactivate(
                database_session,
                user_id=context.user.id,
                password=request.password,
            )
        except InvalidDeactivationPasswordError as error:
            raise ApiError(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code="invalid_credentials",
                message="The supplied credentials are invalid.",
            ) from error
        except AccountCannotBeDeactivatedError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="account_unavailable",
                message="This account cannot be deactivated.",
            ) from error
        return AccountDeactivationResponse(
            account_state="deactivated",
            deactivated_at=result.deactivated_at,
            record_version=result.record_version,
        )

    return router
