from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from achiwave_backend.auth.passwords import PasswordManager
from achiwave_backend.models import DeviceSession, PushToken, RegisteredDevice, User


class InvalidDeactivationPasswordError(Exception):
    """Password confirmation did not match the authenticated account."""


class AccountCannotBeDeactivatedError(Exception):
    """The account is in a state unsupported by this operation."""


@dataclass(frozen=True, slots=True)
class AccountDeactivationResult:
    deactivated_at: datetime
    record_version: int


class AccountDeactivationService:
    def __init__(self, password_manager: PasswordManager) -> None:
        self._password_manager = password_manager

    def deactivate(
        self,
        database_session: Session,
        *,
        user_id: UUID,
        password: str,
    ) -> AccountDeactivationResult:
        user = database_session.scalar(
            select(User).where(User.id == user_id).with_for_update()
        )
        if user is None:
            raise RuntimeError("Authenticated user record is missing.")
        valid, _replacement = self._password_manager.verify(
            password,
            user.password_hash,
        )
        if not valid:
            raise InvalidDeactivationPasswordError
        if user.account_state not in {"active", "deactivated"}:
            raise AccountCannotBeDeactivatedError

        sessions = list(
            database_session.scalars(
                select(DeviceSession)
                .where(
                    DeviceSession.user_id == user.id,
                    DeviceSession.session_state == "active",
                )
                .with_for_update()
            )
        )
        devices = list(
            database_session.scalars(
                select(RegisteredDevice)
                .where(
                    RegisteredDevice.user_id == user.id,
                    RegisteredDevice.device_state == "active",
                )
                .with_for_update()
            )
        )
        push_tokens = list(
            database_session.scalars(
                select(PushToken)
                .where(
                    PushToken.user_id == user.id,
                    PushToken.token_state == "active",
                )
                .with_for_update()
            )
        )
        now = datetime.now(UTC)
        if user.account_state == "active":
            user.account_state = "deactivated"
            user.deactivated_at = now
            user.record_version += 1
            user.updated_at = now
        for device_session in sessions:
            device_session.session_state = "revoked"
            device_session.revoked_at = now
            device_session.revocation_reason = "account_deactivated"
            device_session.record_version += 1
            device_session.updated_at = now
        for device in devices:
            device.device_state = "revoked"
            device.revoked_at = now
            device.revocation_reason = "account_deactivated"
            device.record_version += 1
            device.updated_at = now
        for push_token in push_tokens:
            push_token.token_state = "invalidated"
            push_token.invalidated_at = now
            push_token.invalidation_reason = "account_deactivated"
            push_token.record_version += 1
            push_token.updated_at = now
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        if user.deactivated_at is None:
            raise RuntimeError("Deactivation timestamp is missing.")
        return AccountDeactivationResult(
            deactivated_at=user.deactivated_at,
            record_version=user.record_version,
        )
