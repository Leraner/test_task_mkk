import logging
import traceback
from collections.abc import Callable

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from starlette import status
from starlette.requests import Request
from starlette.responses import JSONResponse

from src.shared.exceptions import InfrastructureError
from src.shared.web.exception_handling.exception_map import (
    DOMAIN_EXCEPTIONS_TO_STATUS_CODES,
    INFRASTRUCTURE_EXCEPTIONS_TO_STATUS_CODES,
    WEB_EXCEPTIONS_TO_STATUS_CODES,
)
from src.shared_kernel.exceptions import DomainError

logger = logging.getLogger(__name__)


def _error_extra(exc: Exception) -> dict[str, str]:
    """Формирует данные об исключении для структурированного лога (не уходят в ответ клиенту)."""
    return {
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "error_traceback": "".join(traceback.TracebackException.from_exception(exc).format()),
    }


def _error_body(exc: Exception) -> dict[str, str]:
    """Формирует тело JSON-ответа об ошибке для клиента: код ошибки и русское сообщение."""
    ru_detail = getattr(exc, "ru_detail", None)
    return {
        "error_code": type(exc).__name__,
        "error_message": ru_detail if ru_detail is not None else str(exc),
    }


def _make_domain_handler(
    status_code: int,
) -> Callable[[Request, DomainError], JSONResponse]:
    """
    Создаёт handler для доменного исключения с заданным статус-кодом.

    Ошибки с кодом >= 500 (например, доменные ошибки, промаппленные на 5xx)
    логируются как error, остальные - как info, т.к. это ожидаемые
    клиентские ошибки, а не сбой сервиса.
    """

    def handler(request: Request, exc: DomainError) -> JSONResponse:
        if status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
            logger.error("Domain error", extra=_error_extra(exc))
        else:
            logger.info("Client error", extra=_error_extra(exc))
        return JSONResponse(status_code=status_code, content=_error_body(exc))

    return handler


def _make_infrastructure_handler(
    status_code: int,
) -> Callable[[Request, InfrastructureError], JSONResponse]:
    """
    Создаёт handler для инфраструктурного исключения с заданным статус-кодом.

    В отличие от доменных ошибок, инфраструктурные всегда логируются как
    error - это сбой зависимости (БД, внешний сервис), а не ожидаемое
    поведение клиента.
    """

    def handler(request: Request, exc: InfrastructureError) -> JSONResponse:
        logger.error("Infrastructure error", extra=_error_extra(exc))
        return JSONResponse(status_code=status_code, content=_error_body(exc))

    return handler


def setup_exception_handlers(app: FastAPI) -> None:
    """
    Регистрирует в приложении FastAPI все exception-handler'ы:
    доменные и инфраструктурные из `exception_map.py`, ошибку валидации
    запроса, а также fallback-handler на любое необработанное исключение.
    """
    for exc_class, status_code in (
        DOMAIN_EXCEPTIONS_TO_STATUS_CODES | WEB_EXCEPTIONS_TO_STATUS_CODES
    ).items():
        app.exception_handler(exc_class)(_make_domain_handler(status_code))

    for exc_class, status_code in INFRASTRUCTURE_EXCEPTIONS_TO_STATUS_CODES.items():
        app.exception_handler(exc_class)(_make_infrastructure_handler(status_code))

    @app.exception_handler(RequestValidationError)
    def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Ошибка валидации входных данных запроса (Pydantic) → 422."""
        logger.warning("Validation error", extra=_error_extra(exc))
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_error_body(exc),
        )

    @app.exception_handler(Exception)
    def unknown_error_handler(request: Request, exc: Exception) -> JSONResponse:
        """Fallback на любое необработанное исключение → 500, без утечки деталей клиенту."""
        logger.error("Unhandled exception", extra=_error_extra(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error_code": type(exc).__name__,
                "error_message": "Произошла непредвиденная ошибка.",
            },
        )
