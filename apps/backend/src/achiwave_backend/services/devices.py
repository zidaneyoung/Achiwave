from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import AuthenticationContext
from achiwave_backend.models import DeviceSession, PushToken, RegisteredDevice
from achiwave_backend.schemas.devices import CurrentDeviceRegistrationRequest


class InvalidCurrentDeviceContextError(Exception):
    """The authenticated session does not match the proposed installation."""


class OwnedRevocationTargetNotFoundError(Exception):
    """A revocation identifier did not resolve inside the authenticated owner."""


@dataclass(frozen=True, slots=True)
class RevocationResult:
    target_type: Literal["device", "session"]
    target_id: UUID
    revoked_at: datetime | None
    already_inactive: bool
    current_session_revoked: bool


class DeviceService:
    def register_current(
        self,
        database_session: Session,
        context: AuthenticationContext,
        request: CurrentDeviceRegistrationRequest,
    ) -> RegisteredDevice:
        device = context.device
        if (
            device.user_id != context.user.id
            or device.id != context.session.device_id
            or device.platform != request.platform
            or device.installation_id != str(request.installation_id)
            or device.app_environment != request.app_environment
        ):
            raise InvalidCurrentDeviceContextError

        now = datetime.now(UTC)
        metadata_changed = (
            device.app_version != request.app_version
            or device.build_version != request.build_version
        )
        device.app_version = request.app_version
        device.build_version = request.build_version
        device.last_seen_at = now
        if metadata_changed:
            device.record_version += 1
            device.updated_at = now
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        database_session.refresh(device)
        return device

    def list_owned(
        self,
        database_session: Session,
        context: AuthenticationContext,
    ) -> list[RegisteredDevice]:
        return list(
            database_session.scalars(
                select(RegisteredDevice)
                .where(RegisteredDevice.user_id == context.user.id)
                .order_by(
                    RegisteredDevice.registered_at.desc(),
                    RegisteredDevice.id,
                )
            )
        )

    def list_sessions(
        self,
        database_session: Session,
        context: AuthenticationContext,
    ) -> list[tuple[DeviceSession, RegisteredDevice]]:
        return list(
            database_session.execute(
                select(DeviceSession, RegisteredDevice)
                .join(
                    RegisteredDevice,
                    RegisteredDevice.id == DeviceSession.device_id,
                )
                .where(
                    DeviceSession.user_id == context.user.id,
                    RegisteredDevice.user_id == context.user.id,
                )
                .order_by(DeviceSession.created_at.desc(), DeviceSession.id)
            ).tuples()
        )

    def revoke_session(
        self,
        database_session: Session,
        context: AuthenticationContext,
        session_id: UUID,
    ) -> RevocationResult:
        target = database_session.scalar(
            select(DeviceSession)
            .where(
                DeviceSession.id == session_id,
                DeviceSession.user_id == context.user.id,
            )
            .with_for_update()
        )
        if target is None:
            raise OwnedRevocationTargetNotFoundError

        already_inactive = target.session_state != "active"
        now = datetime.now(UTC)
        if not already_inactive:
            target.session_state = "revoked"
            target.revoked_at = now
            target.revocation_reason = "user_requested_session_revocation"
            target.record_version += 1
            target.updated_at = now
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return RevocationResult(
            target_type="session",
            target_id=target.id,
            revoked_at=target.revoked_at,
            already_inactive=already_inactive,
            current_session_revoked=target.id == context.session.id,
        )

    def revoke_device(
        self,
        database_session: Session,
        context: AuthenticationContext,
        device_id: UUID,
    ) -> RevocationResult:
        device = database_session.scalar(
            select(RegisteredDevice)
            .where(
                RegisteredDevice.id == device_id,
                RegisteredDevice.user_id == context.user.id,
            )
            .with_for_update()
        )
        if device is None:
            raise OwnedRevocationTargetNotFoundError

        sessions = list(
            database_session.scalars(
                select(DeviceSession)
                .where(
                    DeviceSession.user_id == context.user.id,
                    DeviceSession.device_id == device.id,
                    DeviceSession.session_state == "active",
                )
                .with_for_update()
            )
        )
        push_tokens = list(
            database_session.scalars(
                select(PushToken)
                .where(
                    PushToken.user_id == context.user.id,
                    PushToken.device_id == device.id,
                    PushToken.token_state == "active",
                )
                .with_for_update()
            )
        )
        already_inactive = device.device_state != "active"
        now = datetime.now(UTC)
        if not already_inactive:
            device.device_state = "revoked"
            device.revoked_at = now
            device.revocation_reason = "user_requested_device_revocation"
            device.record_version += 1
            device.updated_at = now
        for target_session in sessions:
            target_session.session_state = "revoked"
            target_session.revoked_at = now
            target_session.revocation_reason = "device_revoked_by_user"
            target_session.record_version += 1
            target_session.updated_at = now
        for push_token in push_tokens:
            push_token.token_state = "invalidated"
            push_token.invalidated_at = now
            push_token.invalidation_reason = "device_revoked_by_user"
            push_token.record_version += 1
            push_token.updated_at = now
        try:
            database_session.commit()
        except Exception:
            database_session.rollback()
            raise
        return RevocationResult(
            target_type="device",
            target_id=device.id,
            revoked_at=device.revoked_at,
            already_inactive=already_inactive,
            current_session_revoked=context.session.device_id == device.id,
        )
