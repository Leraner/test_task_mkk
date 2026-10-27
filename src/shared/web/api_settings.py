from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class APISettings(BaseSettings):
    """
    Класс отвечает за конфигурацию инстанса FastAPI через переменные окружения.

    Любой атрибут класса можно переопределить либо передав значение напрямую
    в конструктор, либо через соответствующую переменную окружения.

    Атрибут `xxx_yyy` соответствует переменной окружения `API_XXX_YYY`. Например,
    чтобы переопределить `openapi_prefix`, нужно задать переменную `API_OPENAPI_PREFIX`.

    Присваивание значений атрибутам также валидируется - даже при изменении
    конфига в рантайме типы данных останутся корректными.
    """

    # fastapi.applications.FastAPI initializer kwargs
    debug: bool = False
    docs_url: str = "/docs"
    openapi_prefix: str = ""
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    title: str = "FastAPI"
    version: str = "0.1.0"

    host: str = "0.0.0.0"
    port: int = 8000

    jwt_secret_key: str = "some_key"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    superadmin_email: str = ""

    # Custom settings
    disable_docs: bool = False
    api_v1_prefix: str = "/api/v1"

    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
        ],
        validation_alias="ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: str | list[str]) -> list[str]:
        """Позволяет задавать `ORIGINS` строкой с адресами через запятую (как в .env)."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",")]
        return value

    @property
    def fastapi_kwargs(self) -> dict[str, Any]:
        """
        Возвращает словарь наиболее часто используемых именованных аргументов
        для инициализации инстанса FastAPI.

        Если `self.disable_docs` равен True, все аргументы, связанные с
        документацией, отключаются, и спецификация API не публикуется.
        """
        fastapi_kwargs: dict[str, Any] = {
            "debug": self.debug,
            "docs_url": self.docs_url,
            "openapi_prefix": self.openapi_prefix,
            "openapi_url": self.openapi_url,
            "redoc_url": self.redoc_url,
            "title": self.title,
            "version": self.version,
        }
        if self.disable_docs:
            fastapi_kwargs.update({"docs_url": None, "openapi_url": None, "redoc_url": None})
        return fastapi_kwargs

    model_config = SettingsConfigDict(validate_assignment=True)


@lru_cache
def get_api_settings() -> APISettings:
    """
    Возвращает закэшированный инстанс APISettings.

    Кэширование используется, чтобы не перечитывать переменные окружения
    при каждом обращении к настройкам API в эндпоинтах.

    Если нужно изменить переменную окружения и сбросить кэш (например, в
    тестах), это можно сделать через `get_api_settings.cache_clear()`.
    """
    return APISettings()
