from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WebhookSettings(BaseSettings):
    """Параметры отправки webhook."""

    model_config = SettingsConfigDict(env_prefix="WEBHOOK_", extra="ignore")

    timeout: float = 5.0


@lru_cache
def get_webhook_settings() -> WebhookSettings:
    """Кэшированный экземпляр настроек. Для сброса - get_webhook_settings.cache_clear()."""
    return WebhookSettings()
