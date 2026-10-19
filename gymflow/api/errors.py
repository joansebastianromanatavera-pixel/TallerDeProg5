"""Global exception handlers. Every error is returned with the ErrorOut shape."""

import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException

from gymflow.api.schemas import ErrorOut

logger = logging.getLogger("gymflow.api")


def _error_response(
    status_code: int, detail: Any, headers: dict[str, str] | None = None
) -> JSONResponse:
    body = ErrorOut(error=HTTPStatus(status_code).phrase, detail=detail, status=status_code)
    return JSONResponse(status_code=status_code, content=body.model_dump(), headers=headers)


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return _error_response(exc.status_code, exc.detail, exc.headers)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    problems = [
        {"field": ".".join(str(part) for part in err["loc"]), "message": err["msg"]}
        for err in exc.errors()
    ]
    return _error_response(status.HTTP_422_UNPROCESSABLE_CONTENT, problems)


async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    logger.warning("Integrity error on %s %s: %s", request.method, request.url.path, exc.orig)
    return _error_response(
        status.HTTP_409_CONFLICT,
        "The request conflicts with existing data (duplicate value or invalid reference).",
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Log the full traceback server-side but never expose it to the client.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR, "An unexpected error occurred. Please try again later."
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)
