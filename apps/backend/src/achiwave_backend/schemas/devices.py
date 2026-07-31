from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from achiwave_backend.schemas.auth import AndroidInstallationRequest


class CurrentDeviceRegistrationRequest(AndroidInstallationRequest):
    pass


class DeviceResponse(BaseModel):
    id: UUID
    label: str
    platform: Literal["android", "ios"]
    app_environment: Literal["development", "preview", "production"]
    app_version: str | None
    build_version: str | None
    device_state: Literal["active", "revoked", "removed"]
    registered_at: datetime
    last_seen_at: datetime | None
    record_version: int
    is_current: bool


class DeviceListResponse(BaseModel):
    devices: list[DeviceResponse]


class SessionResponse(BaseModel):
    id: UUID
    device_id: UUID
    device_label: str
    session_state: Literal["active", "revoked", "expired", "replaced"]
    created_at: datetime
    expires_at: datetime
    last_used_at: datetime | None
    revoked_at: datetime | None
    record_version: int
    is_current: bool


class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]


class RevocationResponse(BaseModel):
    target_type: Literal["device", "session"]
    target_id: UUID
    revoked_at: datetime | None
    already_inactive: bool
    current_session_revoked: bool
