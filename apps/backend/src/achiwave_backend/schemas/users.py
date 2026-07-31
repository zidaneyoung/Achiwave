from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class CurrentUserResponse(BaseModel):
    id: UUID
    email: str
    account_state: Literal["active"]
    record_version: int
