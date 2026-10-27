from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class ConsumerSettings(BaseSettings):
    """Параллельность consumer'а (prefetch) и повторы при сбоях БД."""

    model_config = SettingsConfigDict(env_prefix="CONSUMER_", extra="ignore", env_ignore_empty=True)

    prefetch_count: int = 100
    transient_retry_for: float = 60.0
    transient_retry_max_delay: float = 10.0


@lru_cache
def get_consumer_settings() -> ConsumerSettings:
    """Кэшированный экземпляр настроек. Для сброса - get_consumer_settings.cache_clear()."""
    return ConsumerSettings()
