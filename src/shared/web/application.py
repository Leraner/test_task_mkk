import logging

import uvicorn
from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.shared.di.di_container import container
from src.shared.web.api_settings import APISettings
from src.shared.web.exception_handling.exception_handlers import (
    setup_exception_handlers,
)
from src.shared.web.middlewares.cors_middleware import get_cors_middleware_kwargs
from src.shared.web.routes.router import router

logger = logging.getLogger(__name__)


class Application:
    """
    Фабрика FastAPI-приложения.

    Собирает инстанс `FastAPI` из `APISettings`: подключает DI-контейнер
    (dishka), middleware, общий роутер со всеми bounded contexts и
    exception-handler'ы. Также умеет запускать приложение через uvicorn
    (`run`) - используется как единая точка входа для локального запуска.
    """

    def __init__(self, settings: APISettings) -> None:
        self._settings = settings

    def _add_middlewares(self, application: FastAPI) -> None:
        """Подключает middleware к приложению"""
        application.add_middleware(
            CORSMiddleware,
            **get_cors_middleware_kwargs(self._settings),
        )

    def _create_application(self) -> FastAPI:
        """Создаёт и полностью настраивает инстанс FastAPI, готовый к запуску."""
        application = FastAPI(
            title=self._settings.title,
            version=self._settings.version,
            docs_url=self._settings.docs_url,
            redoc_url=self._settings.redoc_url,
            openapi_url=self._settings.openapi_url,
        )
        setup_dishka(app=application, container=container)
        self._add_middlewares(application)
        application.include_router(router)
        setup_exception_handlers(application)
        return application

    def run(self):
        """Создаёт приложение и запускает его через uvicorn на host/port из настроек."""
        application = self._create_application()
        logger.info(
            "application_starting",
            extra={
                "host": self._settings.host,
                "port": self._settings.port,
            },
        )
        uvicorn.run(
            app=application,
            host=self._settings.host,
            port=self._settings.port,
            log_level=logging.WARNING,
        )
