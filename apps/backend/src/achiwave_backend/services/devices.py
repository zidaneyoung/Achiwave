from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import AuthenticationContext
from achiwave_backend.models import RegisteredDevice
from achiwave_backend.schemas.devices import CurrentDeviceRegistrationRequest


class InvalidCurrentDeviceContextError(Exception):
    """The authenticated session does not match the proposed installation."""


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
