from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitSettings(BaseSettings):
    """Подключение к RabbitMQ; логин и пароль - те же RABBITMQ_DEFAULT_*, что у контейнера."""

    model_config = SettingsConfigDict(env_prefix="RABBITMQ_", extra="ignore")

    default_user: str = "guest"
    default_pass: str = "guest"
    host: str = "rabbitmq"
    port: int = 5672

    @property
    def url(self) -> str:
        """Строка подключения вида amqp://user:password@host:port/."""
        return f"amqp://{self.default_user}:{self.default_pass}@{self.host}:{self.port}/"


@lru_cache
def get_rabbit_settings() -> RabbitSettings:
    """Кэшированный экземпляр настроек. Для сброса - get_rabbit_settings.cache_clear()."""
    return RabbitSettings()
