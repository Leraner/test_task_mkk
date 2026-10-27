from functools import lru_cache
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    """Подключение к PostgreSQL."""

    model_config = SettingsConfigDict(env_prefix="POSTGRES_", extra="ignore", env_ignore_empty=True)

    user: str
    password: str
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
        user, password = quote(self.user, safe=""), quote(self.password, safe="")
        return f"{self.dialect}+{self.driver}://{user}:{password}@{self.host}:{self.port}/{self.db}"


@lru_cache
def get_db_settings() -> DBSettings:
    """Кэшированный экземпляр настроек. Для сброса - get_db_settings.cache_clear()."""
    return DBSettings()
