from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class PaymentsQueuesSettings(BaseSettings):
    """Топология платежей в RabbitMQ и повторы webhook; переменные без префикса."""

    model_config = SettingsConfigDict(extra="ignore", env_ignore_empty=True)

    payments_exchange: str = "payments"
    payments_new_queue: str = "payments.new"
    payments_new_dlq: str = "payments.new.dlq"
    payments_new_retry_queue_prefix: str = "payments.new.retry"
    # Попыток доставить webhook, включая первую; retry-очередей на одну меньше.
    payments_max_attempts: int = 4
    payments_retry_base_delay_ms: int = 2000


@lru_cache
def get_payments_queues_settings() -> PaymentsQueuesSettings:
    """Кэшированный экземпляр настроек. Для сброса - get_payments_queues_settings.cache_clear()."""
    return PaymentsQueuesSettings()
