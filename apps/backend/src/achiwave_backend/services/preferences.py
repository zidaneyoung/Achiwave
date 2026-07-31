from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.orm import Session

from achiwave_backend.models import User, UserPreference
from achiwave_backend.schemas.preferences import (
    UpdatePresentationPreferencesRequest,
    UpdateTimezoneRequest,
)


class InvalidTimezoneError(Exception):
    """The proposed value is not an accepted named IANA timezone."""


class StalePreferenceVersionError(Exception):
    """The submitted preference version is not current."""


def validate_timezone_name(timezone_name: str) -> None:
    if (
        timezone_name != timezone_name.strip()
        or (timezone_name != "UTC" and "/" not in timezone_name)
        or timezone_name.startswith("Etc/")
    ):
        raise InvalidTimezoneError
    try:
        ZoneInfo(timezone_name)
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise InvalidTimezoneError from error


class PreferenceService:
    def get_current(
        self,
        database_session: Session,
        current_user: User,
    ) -> UserPreference:
        preference = database_session.get(UserPreference, current_user.id)
        if preference is None:
            raise RuntimeError("Active user preference record is missing.")
        return preference

    def update_timezone(
        self,
        database_session: Session,
        current_user: User,
        request: UpdateTimezoneRequest,
    ) -> UserPreference:
        validate_timezone_name(request.timezone_name)
        preference = database_session.scalar(
            select(UserPreference)
            .where(UserPreference.user_id == current_user.id)
            .with_for_update()
        )
        if preference is None:
            raise RuntimeError("Active user preference record is missing.")
        if preference.record_version != request.record_version:
            raise StalePreferenceVersionError
        if preference.timezone_name != request.timezone_name:
            now = datetime.now(UTC)
            preference.timezone_name = request.timezone_name
            preference.timezone_version += 1
            preference.timezone_effective_at = now
            preference.record_version += 1
            preference.updated_at = now
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return preference

    def update_presentation(
        self,
        database_session: Session,
        current_user: User,
        request: UpdatePresentationPreferencesRequest,
    ) -> UserPreference:
        preference = database_session.scalar(
            select(UserPreference)
            .where(UserPreference.user_id == current_user.id)
            .with_for_update()
        )
        if preference is None:
            raise RuntimeError("Active user preference record is missing.")
        if preference.record_version != request.record_version:
            raise StalePreferenceVersionError
        if preference.date_format != request.date_format:
            now = datetime.now(UTC)
            preference.date_format = request.date_format
            preference.record_version += 1
            preference.updated_at = now
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return preference
