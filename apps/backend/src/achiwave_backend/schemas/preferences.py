from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator


class PreferenceResponse(BaseModel):
    timezone_name: str
    timezone_version: int
    timezone_effective_at: datetime
    notification_preference: Literal["unspecified", "enabled", "disabled"]
    date_format: Literal[
        "system",
        "day_month_year",
        "month_day_year",
        "year_month_day",
    ]
    sound_enabled: bool
    haptics_enabled: bool
    reduced_motion: Literal["system", "reduce", "allow"]
    record_version: int


class UpdateTimezoneRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timezone_name: str = Field(min_length=1, max_length=128)
    record_version: int = Field(ge=1)


class UpdatePresentationPreferencesRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date_format: Literal[
        "system",
        "day_month_year",
        "month_day_year",
        "year_month_day",
    ] | None = None
    sound_enabled: StrictBool | None = None
    haptics_enabled: StrictBool | None = None
    reduced_motion: Literal["system", "reduce", "allow"] | None = None
    notification_preference: Literal["unspecified", "enabled", "disabled"] | None = None
    record_version: int = Field(ge=1)

    @model_validator(mode="after")
    def require_non_null_update(self) -> "UpdatePresentationPreferencesRequest":
        update_fields = self.model_fields_set - {"record_version"}
        if not update_fields or any(getattr(self, field) is None for field in update_fields):
            raise ValueError("At least one non-null preference is required.")
        return self
