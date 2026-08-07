from dataclasses import dataclass

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    code: str
    message: str


@dataclass(slots=True)
class ApiError(Exception):
    status_code: int
    code: str
    message: str
    headers: dict[str, str] | None = None
    details: dict[str, object] | None = None


async def api_error_handler(_: Request, error: ApiError) -> JSONResponse:
    content: dict[str, object] = ErrorResponse(
        code=error.code,
        message=error.message,
    ).model_dump()
    if error.details:
        content.update(error.details)
    return JSONResponse(
        status_code=error.status_code,
        content=content,
        headers=error.headers,
    )


async def validation_error_handler(
    _: Request,
    __: RequestValidationError,
) -> JSONResponse:
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        content=ErrorResponse(
            code="validation_error",
            message="The request contains invalid values.",
        ).model_dump(),
    )
