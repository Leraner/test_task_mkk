from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class OutboxRelaySettings(BaseSettings):
    """Параметры цикла outbox relay."""

    model_config = SettingsConfigDict(env_prefix="OUTBOX_", extra="ignore", env_ignore_empty=True)

    batch_size: int = 100
    poll_interval: float = 1.0
    max_backoff: float = 30.0


@lru_cache
def get_outbox_relay_settings() -> OutboxRelaySettings:
    """Кэшированный экземпляр настроек. Для сброса - get_outbox_relay_settings.cache_clear()."""
    return OutboxRelaySettings()
