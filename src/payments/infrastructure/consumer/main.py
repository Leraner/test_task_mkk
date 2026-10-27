import asyncio
import logging

from dishka import make_async_container
from dishka_faststream import FastStreamProvider, FromDishka, setup_dishka
from faststream import AckPolicy, FastStream
from faststream.exceptions import NackMessage
from faststream.rabbit import Channel, RabbitBroker
from faststream.rabbit.annotations import RabbitMessage
from sqlalchemy.exc import InterfaceError, OperationalError
from sqlalchemy.exc import TimeoutError as PoolTimeoutError
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    retry_if_exception_type,
    stop_after_delay,
    wait_exponential_jitter,
)

from src.payments.application.use_cases.process_payment import ProcessPaymentUseCase
from src.payments.domain.exceptions import WebhookDeliveryError
from src.payments.infrastructure.consumer.messages import PaymentCreatedMessage
from src.payments.infrastructure.consumer.provider import ConsumerProvider
from src.payments.infrastructure.consumer.settings import get_consumer_settings
from src.payments.infrastructure.messaging.queues import (
    PAYMENTS_EXCHANGE,
    PAYMENTS_NEW_DLQ,
    PAYMENTS_NEW_QUEUE,
    PAYMENTS_NEW_RETRY_QUEUES,
)
from src.shared.broker.rabbit_settings import get_rabbit_settings
from src.shared.db.provider import DbProvider

# Временные сбои БД (включая переполненный пул): повторяем, в DLQ не отправляем.
TRANSIENT_ERRORS = (OperationalError, InterfaceError, PoolTimeoutError, OSError)

# Номер повтора webhook; RabbitMQ сохраняет заголовки при dead-letter.
RETRY_COUNT_HEADER = "x-retry-count"

logger = logging.getLogger(__name__)

settings = get_consumer_settings()
# on_return_raises: публикация в несуществующую retry-очередь упадёт, а не потеряется.
broker = RabbitBroker(
    get_rabbit_settings().url,
    default_channel=Channel(prefetch_count=settings.prefetch_count, on_return_raises=True),
)
app = FastStream(broker)
container = make_async_container(DbProvider(), ConsumerProvider(), FastStreamProvider())
setup_dishka(container, app, auto_inject=True, finalize_container=True)


@app.on_startup
async def declare_queues() -> None:
    """Объявляем до начала потребления: dead-letter в несуществующую очередь теряется."""
    await broker.connect()
    for queue in (PAYMENTS_NEW_DLQ, *PAYMENTS_NEW_RETRY_QUEUES):
        await broker.declare_queue(queue)


def log_transient_retry(state: RetryCallState) -> None:
    logger.warning(
        "Payment processing hit a transient error (attempt %d), retrying: %r",
        state.attempt_number,
        state.outcome.exception() if state.outcome else None,
    )


# Успех - ack; сбой БД - повторы, затем nack с requeue; webhook не дошёл - копия
# в retry-очередь, после последней попытки - DLQ; остальные ошибки - reject в DLQ.
@broker.subscriber(PAYMENTS_NEW_QUEUE, PAYMENTS_EXCHANGE, ack_policy=AckPolicy.REJECT_ON_ERROR)
async def handle_payment_created(
    message: PaymentCreatedMessage,
    raw_message: RabbitMessage,
    use_case: FromDishka[ProcessPaymentUseCase],
) -> None:
    try:
        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(TRANSIENT_ERRORS),
            wait=wait_exponential_jitter(initial=1, max=settings.transient_retry_max_delay),
            stop=stop_after_delay(settings.transient_retry_for),
            before_sleep=log_transient_retry,
            reraise=True,
        ):
            with attempt:
                result = await use_case.execute(message.to_dto())
    except TRANSIENT_ERRORS as err:
        logger.error("Payment %s: transient error persists, requeue: %r", message.payment_id, err)
        raise NackMessage(requeue=True) from err
    except WebhookDeliveryError as err:
        retry = int(raw_message.headers.get(RETRY_COUNT_HEADER, 0)) + 1
        if retry > len(PAYMENTS_NEW_RETRY_QUEUES):
            logger.error(
                "Payment %s: webhook failed after %d attempts, to DLQ: %s",
                message.payment_id,
                retry,
                err.extra,
            )
            raise
        retry_queue = PAYMENTS_NEW_RETRY_QUEUES[retry - 1]
        # Сначала копия, потом ack: упадём между ними - будет дубль, а не потеря.
        await broker.publish(
            message.model_dump(mode="json"),
            queue=retry_queue,
            headers={RETRY_COUNT_HEADER: retry},
            message_id=raw_message.message_id,
            persist=True,
        )
        logger.warning(
            "Payment %s: webhook failed (attempt %d), retry via %s: %s",
            message.payment_id,
            retry,
            retry_queue.name,
            err.extra,
        )
        return

    logger.info("Payment %s processed: %s", result.payment_id, result.status)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(app.run())
