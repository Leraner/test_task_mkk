import asyncio

from faststream.rabbit import RabbitBroker

from src.payments.domain.interfaces.unit_of_work import IPaymentsUnitOfWork
from src.payments.infrastructure.messaging.queues import PAYMENTS_EXCHANGE


class OutboxRelay:
    """Публикует события из outbox; `published_at` ставится только после подтверждения брокера."""

    def __init__(self, uow: IPaymentsUnitOfWork, broker: RabbitBroker) -> None:
        self._uow = uow
        self._broker = broker

    async def publish_batch(self, limit: int) -> int:
        """Публикует до `limit` неотправленных событий и возвращает их количество."""
        async with self._uow:
            messages = await self._uow.outbox.get_unpublished_for_update(limit)
            async with asyncio.TaskGroup() as tg:
                for message in messages:
                    tg.create_task(
                        self._broker.publish(
                            message.payload,
                            exchange=PAYMENTS_EXCHANGE,
                            routing_key=message.routing_key,
                            message_id=str(message.id),
                            persist=True,
                        )
                    )
            if messages:
                await self._uow.outbox.mark_published([message.id for message in messages])
                await self._uow.commit()
        return len(messages)
