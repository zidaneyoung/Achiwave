from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from achiwave_backend.models import User
from achiwave_backend.schemas.users import UpdateCurrentUserRequest


class StaleProfileVersionError(Exception):
    """The submitted profile version is not current."""


class ProfileService:
    def update_current(
        self,
        database_session: Session,
        current_user: User,
        request: UpdateCurrentUserRequest,
    ) -> User:
        user = database_session.scalar(
            select(User)
            .where(User.id == current_user.id)
            .with_for_update()
        )
        if user is None:
            raise RuntimeError("Authenticated user record is missing.")
        if user.record_version != request.record_version:
            raise StaleProfileVersionError
        if user.display_name != request.display_name:
            user.display_name = request.display_name
            user.record_version += 1
            user.updated_at = datetime.now(UTC)
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return user
