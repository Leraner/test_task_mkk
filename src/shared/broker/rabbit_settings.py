from functools import lru_cache
from urllib.parse import quote

from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitSettings(BaseSettings):
    """Подключение к RabbitMQ; логин и пароль - те же RABBITMQ_DEFAULT_*, что у контейнера."""

    model_config = SettingsConfigDict(env_prefix="RABBITMQ_", extra="ignore", env_ignore_empty=True)

    default_user: str
    default_pass: str
    host: str = "rabbitmq"
    port: int = 5672

    @property
    def url(self) -> str:
        """Строка подключения вида amqp://user:password@host:port/."""
        user, password = quote(self.default_user, safe=""), quote(self.default_pass, safe="")
        return f"amqp://{user}:{password}@{self.host}:{self.port}/"


@lru_cache
def get_rabbit_settings() -> RabbitSettings:
    """Кэшированный экземпляр настроек. Для сброса - get_rabbit_settings.cache_clear()."""
    return RabbitSettings()
