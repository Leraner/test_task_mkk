from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WebhookSettings(BaseSettings):
    """Параметры отправки webhook; приватные адреса разрешать только в тестовом окружении."""

    model_config = SettingsConfigDict(env_prefix="WEBHOOK_", extra="ignore", env_ignore_empty=True)

    timeout: float = 5.0
    allow_private_networks: bool = False


@lru_cache
def get_webhook_settings() -> WebhookSettings:
    """Кэшированный экземпляр настроек. Для сброса - get_webhook_settings.cache_clear()."""
    return WebhookSettings()
