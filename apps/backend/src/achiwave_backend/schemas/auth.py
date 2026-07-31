from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class AndroidInstallationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    installation_id: UUID
    platform: Literal["android"] = "android"
    app_environment: Literal["development", "preview", "production"]
    app_version: str | None = Field(default=None, min_length=1, max_length=64)
    build_version: str | None = Field(default=None, min_length=1, max_length=64)


class RegistrationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)
    timezone_name: str | None = Field(default=None, min_length=1, max_length=128)
    installation: AndroidInstallationRequest

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=1, max_length=1024)
    installation: AndroidInstallationRequest

    @field_validator("email", mode="before")
    @classmethod
    def trim_email(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class RefreshRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str = Field(min_length=43, max_length=512)
    installation: AndroidInstallationRequest


class LogoutRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    refresh_token: str | None = Field(default=None, min_length=43, max_length=512)


class SafeUserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str | None
    account_state: Literal["active"]
    record_version: int


class RegistrationResponse(BaseModel):
    user: SafeUserResponse
    timezone_name: str
    timezone_was_defaulted: bool
    device_id: UUID
    session_id: UUID
    session_expires_at: datetime
    access_token: str
    access_token_expires_at: datetime
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class LoginResponse(BaseModel):
    user: SafeUserResponse
    timezone_name: str
    device_id: UUID
    session_id: UUID
    session_expires_at: datetime
    access_token: str
    access_token_expires_at: datetime
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"


class RefreshResponse(BaseModel):
    session_id: UUID
    session_expires_at: datetime
    access_token: str
    access_token_expires_at: datetime
    refresh_token: str
    token_type: Literal["bearer"] = "bearer"
