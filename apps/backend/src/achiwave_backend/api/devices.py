from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from achiwave_backend.api.dependencies import (
    AuthenticationContext,
    AuthenticationDependencies,
)
from achiwave_backend.api.errors import ApiError, ErrorResponse
from achiwave_backend.models import DeviceSession, RegisteredDevice
from achiwave_backend.schemas.devices import (
    CurrentDeviceRegistrationRequest,
    DeviceListResponse,
    DeviceResponse,
    RevocationResponse,
    SessionListResponse,
    SessionResponse,
)
from achiwave_backend.services.devices import (
    DeviceService,
    InvalidCurrentDeviceContextError,
    OwnedRevocationTargetNotFoundError,
    RevocationResult,
)


def _device_response(
    device: RegisteredDevice,
    *,
    current_device_id: UUID,
) -> DeviceResponse:
    return DeviceResponse(
        id=device.id,
        label=f"{device.platform.capitalize()} device",
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


def _session_response(
    device_session: DeviceSession,
    device: RegisteredDevice,
    *,
    current_session_id: UUID,
) -> SessionResponse:
    return SessionResponse(
        id=device_session.id,
        device_id=device.id,
        device_label=f"{device.platform.capitalize()} device",
        session_state=device_session.session_state,
        created_at=device_session.created_at,
        expires_at=device_session.expires_at,
        last_used_at=device_session.last_used_at,
        revoked_at=device_session.revoked_at,
        record_version=device_session.record_version,
        is_current=device_session.id == current_session_id,
    )


def _revocation_response(result: RevocationResult) -> RevocationResponse:
    return RevocationResponse(
        target_type=result.target_type,
        target_id=result.target_id,
        revoked_at=result.revoked_at,
        already_inactive=result.already_inactive,
        current_session_revoked=result.current_session_revoked,
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

    @router.post(
        "/{device_id}/revoke",
        response_model=RevocationResponse,
        responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
    )
    def revoke_device(
        device_id: UUID,
        context: AuthenticationContext = Depends(authentication.current_context),
        database_session: Session = Depends(authentication.database_session),
    ) -> RevocationResponse:
        try:
            result = service.revoke_device(database_session, context, device_id)
        except OwnedRevocationTargetNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="not_found",
                message="The requested device was not found.",
            ) from error
        return _revocation_response(result)

    return router


def create_sessions_router(
    authentication: AuthenticationDependencies,
) -> APIRouter:
    router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])
    service = DeviceService()

    @router.get("", response_model=SessionListResponse)
    def list_sessions(
        context: AuthenticationContext = Depends(authentication.current_context),
        database_session: Session = Depends(authentication.database_session),
    ) -> SessionListResponse:
        sessions = service.list_sessions(database_session, context)
        return SessionListResponse(
            sessions=[
                _session_response(
                    device_session,
                    device,
                    current_session_id=context.session.id,
                )
                for device_session, device in sessions
            ]
        )

    @router.post(
        "/{session_id}/revoke",
        response_model=RevocationResponse,
        responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse}},
    )
    def revoke_session(
        session_id: UUID,
        context: AuthenticationContext = Depends(authentication.current_context),
        database_session: Session = Depends(authentication.database_session),
    ) -> RevocationResponse:
        try:
            result = service.revoke_session(database_session, context, session_id)
        except OwnedRevocationTargetNotFoundError as error:
            raise ApiError(
                status_code=status.HTTP_404_NOT_FOUND,
                code="not_found",
                message="The requested session was not found.",
            ) from error
        return _revocation_response(result)

    return router
