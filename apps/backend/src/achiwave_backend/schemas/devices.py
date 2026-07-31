from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from achiwave_backend.schemas.auth import AndroidInstallationRequest


class CurrentDeviceRegistrationRequest(AndroidInstallationRequest):
    pass


class DeviceResponse(BaseModel):
    id: UUID
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
