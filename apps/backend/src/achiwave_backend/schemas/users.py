import unicodedata
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CurrentUserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str | None
    account_state: Literal["active"]
    record_version: int


class UpdateCurrentUserRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None
    record_version: int = Field(ge=1)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if value != value.strip() or "  " in value:
            raise ValueError("Display name whitespace is invalid.")
        if not 1 <= len(value) <= 80:
            raise ValueError("Display name length is invalid.")
        for character in value:
            category = unicodedata.category(character)
            if (
                character != " "
                and character not in "'-."
                and category[0] not in {"L", "M", "N"}
            ):
                raise ValueError("Display name contains unsupported characters.")
        return value
