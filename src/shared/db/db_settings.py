"""Настройки подключения к PostgreSQL, читаемые из переменных окружения с префиксом `POSTGRES_`."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    """
    Параметры подключения к PostgreSQL.

    Каждый атрибут `xxx` соответствует переменной окружения `POSTGRES_XXX`
    (например, `host` → `POSTGRES_HOST`). Значения по умолчанию рассчитаны
    на локальный docker-compose стек.
    """

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore")

    user: str = "postgres"
    password: str = "postgres"
    db: str = "postgres"
    port: int = 5432
    host: str = "database"
    dialect: str = "postgresql"
    driver: str = "asyncpg"
    pool_pre_ping: bool = True
    pool_recycle: int = 1800

    @property
    def connection_url(self) -> str:
        """Строка подключения вида dialect+driver://user:password@host:port/db."""
        return (
            f"{self.dialect}+{self.driver}:"
            f"//{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.db}"
        )


@lru_cache
def get_db_settings() -> DBSettings:
    """Кэшированный экземпляр настроек. Для сброса — get_db_settings.cache_clear()."""
    return DBSettings()
