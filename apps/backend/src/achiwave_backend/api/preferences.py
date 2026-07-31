from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import AuthenticationDependencies
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.models import User, UserPreference
from achiwave_backend.schemas.preferences import (
    PreferenceResponse,
    UpdatePresentationPreferencesRequest,
    UpdateTimezoneRequest,
)
from achiwave_backend.services.preferences import (
    InvalidTimezoneError,
    PreferenceService,
    StalePreferenceVersionError,
)


def _preference_response(preference: UserPreference) -> PreferenceResponse:
    return PreferenceResponse(
        timezone_name=preference.timezone_name,
        timezone_version=preference.timezone_version,
        timezone_effective_at=preference.timezone_effective_at,
        notification_preference=preference.notification_preference,
        date_format=preference.date_format,
        record_version=preference.record_version,
    )


def create_preferences_router(
    authentication: AuthenticationDependencies,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/preferences", tags=["preferences"])
    service = PreferenceService()

    @router.get("", response_model=PreferenceResponse)
    def get_preferences(
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> PreferenceResponse:
        return _preference_response(service.get_current(database_session, user))

    @router.patch(
        "",
        response_model=PreferenceResponse,
        responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
    )
    def update_presentation_preferences(
        request: UpdatePresentationPreferencesRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> PreferenceResponse:
        try:
            preference = service.update_presentation(database_session, user, request)
        except StalePreferenceVersionError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message="Preferences changed before this update was applied.",
            ) from error
        return _preference_response(preference)

    @router.patch(
        "/timezone",
        response_model=PreferenceResponse,
        responses={
            status.HTTP_409_CONFLICT: {"model": ErrorResponse},
            status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
        },
    )
    def update_timezone(
        request: UpdateTimezoneRequest,
        user: User = Depends(authentication.current_user),
        database_session: Session = Depends(authentication.database_session),
    ) -> PreferenceResponse:
        try:
            preference = service.update_timezone(database_session, user, request)
        except InvalidTimezoneError as error:
            raise ApiError(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                code="invalid_timezone",
                message="Select a valid named IANA timezone.",
            ) from error
        except StalePreferenceVersionError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="stale_record_version",
                message="Preferences changed before this update was applied.",
            ) from error
        return _preference_response(preference)

    return router
