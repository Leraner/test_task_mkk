from faststream.rabbit import ExchangeType, RabbitExchange, RabbitQueue

from src.payments.infrastructure.messaging.settings import get_payments_queues_settings

settings = get_payments_queues_settings()

# Контракт между outbox relay и consumer'ом, поэтому константа, а не настройка.
PAYMENT_CREATED_ROUTING_KEY = "payment.created"

PAYMENTS_EXCHANGE = RabbitExchange(
    settings.payments_exchange, type=ExchangeType.DIRECT, durable=True
)

PAYMENTS_NEW_DLQ = RabbitQueue(settings.payments_new_dlq, durable=True)

# Привязана к PAYMENTS_EXCHANGE по routing key события «платёж создан».
# Отвергнутые consumer'ом сообщения (reject без requeue) уходят через default exchange в DLQ.
PAYMENTS_NEW_QUEUE = RabbitQueue(
    settings.payments_new_queue,
    durable=True,
    routing_key=PAYMENT_CREATED_ROUTING_KEY,
    arguments={
        "x-dead-letter-exchange": "",
        "x-dead-letter-routing-key": PAYMENTS_NEW_DLQ.name,
    },
)


def _retry_queue(retry: int) -> RabbitQueue:
    """Очередь отложенного повтора: по истечении TTL сообщение возвращается в payments.new."""
    return RabbitQueue(
        f"{settings.payments_new_retry_queue_prefix}.{retry}",
        durable=True,
        arguments={
            "x-message-ttl": settings.payments_retry_base_delay_ms * 2 ** (retry - 1),
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": PAYMENTS_NEW_QUEUE.name,
        },
    )


# По умолчанию: retry.1 - 2 с, retry.2 - 4 с, retry.3 - 8 с, потом DLQ.
PAYMENTS_NEW_RETRY_QUEUES = tuple(
    _retry_queue(retry) for retry in range(1, settings.payments_max_attempts)
)
