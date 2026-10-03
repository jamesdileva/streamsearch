"""Basic error model: every error is {"error": {"code", "message"}}."""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: int
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


def _envelope(status_code: int, message: str) -> dict:
    return ErrorResponse(
        error=ErrorDetail(code=status_code, message=message)
    ).model_dump()


async def _http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code, content=_envelope(exc.status_code, detail)
    )


async def _unhandled_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content=_envelope(500, "internal error"))


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _unhandled_handler)
