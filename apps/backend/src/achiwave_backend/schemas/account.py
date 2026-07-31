from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AccountDeactivationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    password: str = Field(min_length=1, max_length=1024)


class AccountDeactivationResponse(BaseModel):
    account_state: Literal["deactivated"]
    deactivated_at: datetime
    record_version: int
