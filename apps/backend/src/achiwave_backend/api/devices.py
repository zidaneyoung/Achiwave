from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import (
    AuthenticationContext,
    AuthenticationDependencies,
)
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.models import RegisteredDevice
from achiwave_backend.schemas.devices import (
    CurrentDeviceRegistrationRequest,
    DeviceListResponse,
    DeviceResponse,
)
from achiwave_backend.services.devices import (
    DeviceService,
    InvalidCurrentDeviceContextError,
)


def _device_response(
    device: RegisteredDevice,
    *,
    current_device_id: object,
) -> DeviceResponse:
    return DeviceResponse(
        id=device.id,
        platform=device.platform,
        app_environment=device.app_environment,
        app_version=device.app_version,
        build_version=device.build_version,
        device_state=device.device_state,
        registered_at=device.registered_at,
        last_seen_at=device.last_seen_at,
        record_version=device.record_version,
        is_current=device.id == current_device_id,
    )


def create_devices_router(
    authentication: AuthenticationDependencies,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/devices", tags=["devices"])
    service = DeviceService()

    @router.put(
        "/current",
        response_model=DeviceResponse,
        responses={status.HTTP_409_CONFLICT: {"model": ErrorResponse}},
    )
    def register_current_device(
        request: CurrentDeviceRegistrationRequest,
        context: AuthenticationContext = Depends(authentication.current_context),
        database_session: Session = Depends(authentication.database_session),
    ) -> DeviceResponse:
        try:
            device = service.register_current(database_session, context, request)
        except InvalidCurrentDeviceContextError as error:
            raise ApiError(
                status_code=status.HTTP_409_CONFLICT,
                code="invalid_device_context",
                message="The authenticated device context does not match.",
            ) from error
        return _device_response(device, current_device_id=context.device.id)

    @router.get("", response_model=DeviceListResponse)
    def list_devices(
        context: AuthenticationContext = Depends(authentication.current_context),
        database_session: Session = Depends(authentication.database_session),
    ) -> DeviceListResponse:
        devices = service.list_owned(database_session, context)
        return DeviceListResponse(
            devices=[
                _device_response(device, current_device_id=context.device.id)
                for device in devices
            ]
        )

    return router
