from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


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
    ]
    record_version: int = Field(ge=1)
