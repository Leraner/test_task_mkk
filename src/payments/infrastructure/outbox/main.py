import asyncio
import logging

from dishka import make_async_container
from faststream import FastStream
from faststream.rabbit import Channel, RabbitBroker

from src.payments.infrastructure.messaging.queues import PAYMENTS_EXCHANGE
from src.payments.infrastructure.outbox.provider import OutboxRelayProvider
from src.payments.infrastructure.outbox.relay import OutboxRelay
from src.payments.infrastructure.outbox.settings import get_outbox_relay_settings
from src.shared.broker.rabbit_settings import get_rabbit_settings
from src.shared.db.provider import DbProvider

logger = logging.getLogger(__name__)

broker = RabbitBroker(
    get_rabbit_settings().url,
    default_channel=Channel(on_return_raises=True),
)
app = FastStream(broker)
container = make_async_container(
    DbProvider(),
    OutboxRelayProvider(),
    context={RabbitBroker: broker},
)
relay_task: asyncio.Task[None] | None = None


async def relay_forever() -> None:
    """Цикл relay; при ошибках подряд пауза удваивается до max_backoff."""
    settings = get_outbox_relay_settings()
    failures = 0
    while True:
        try:
            async with container() as request_container:
                relay = await request_container.get(OutboxRelay)
                published = await relay.publish_batch(settings.batch_size)
        except Exception as err:
            failures += 1
            delay = min(settings.poll_interval * 2 ** (failures - 1), settings.max_backoff)
            # Ошибки публикации приходят из TaskGroup в ExceptionGroup.
            errors = err.exceptions if isinstance(err, ExceptionGroup) else (err,)
            logger.warning(
                "Outbox relay iteration failed (%d in a row), retry in %.1fs: %s",
                failures,
                delay,
                "; ".join(repr(e) for e in errors),
                exc_info=failures == 1,
            )
            await asyncio.sleep(delay)
            continue

        if failures:
            logger.info("Outbox relay recovered after %d failed iterations", failures)
            failures = 0
        if published:
            logger.info("Outbox relay published %d events", published)
        if published < settings.batch_size:
            await asyncio.sleep(settings.poll_interval)


@app.after_startup
async def start_relay() -> None:
    global relay_task
    # Очереди и binding'и объявляет consumer.
    await broker.declare_exchange(PAYMENTS_EXCHANGE)
    relay_task = asyncio.create_task(relay_forever())


@app.on_shutdown
async def stop_relay() -> None:
    if relay_task is not None:
        relay_task.cancel()
        await asyncio.gather(relay_task, return_exceptions=True)
    await container.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    asyncio.run(app.run())
