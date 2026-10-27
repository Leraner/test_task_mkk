from uuid import UUID

from sqlalchemy import func, update

from src.payments.domain.entities import Payment
from src.payments.domain.events import PaymentCreated
from src.payments.domain.exceptions import (
    PaymentAlreadyExistsError,
    PaymentNotFoundError,
)
from src.payments.domain.interfaces.outbox import OutboxMessage
from src.payments.infrastructure.db.models import (
    IDEMPOTENCY_KEY_CONSTRAINT,
    OutboxEventDBModel,
    PaymentDBModel,
)
from src.payments.infrastructure.db.specifications import (
    LockedOutboxBatchSpec,
    OutboxByIdsSpec,
    PaymentByIdempotencyKeySpec,
    PaymentByIdSpec,
    PendingPaymentSpec,
    UnpublishedOutboxSpec,
)
from src.payments.infrastructure.messaging.queues import PAYMENT_CREATED_ROUTING_KEY
from src.shared.db.base.repository import BaseRepository
from src.shared.db.exceptions import DatabaseError


class PaymentsRepository(BaseRepository[PaymentDBModel, Payment]):
    model = PaymentDBModel

    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        return await self._get_one_by_specs([PaymentByIdSpec(payment_id)])

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment:
        payment = await self._get_one_by_specs([PaymentByIdempotencyKeySpec(idempotency_key)])
        if payment is None:
            raise PaymentNotFoundError(idempotency_key=idempotency_key)
        return payment

    async def add(self, payment: Payment) -> Payment:
        try:
            return await self._save_with_return(PaymentDBModel.from_entity(payment))
        except DatabaseError as err:
            if err.is_unique_violation(IDEMPOTENCY_KEY_CONSTRAINT):
                raise PaymentAlreadyExistsError(idempotency_key=payment.idempotency_key)
            raise

    async def save_processing_result(self, payment: Payment) -> bool:
        """Условный UPDATE `WHERE status = 'PENDING'`: результат запишет только первая обработка."""
        query = update(self.model).values(status=payment.status, processed_at=payment.processed_at)
        query = self._apply_specs(
            query=query, specs=[PaymentByIdSpec(payment.id), PendingPaymentSpec()]
        )
        result = await self._execute(query)
        return result.rowcount == 1


class OutboxRepository(BaseRepository[OutboxEventDBModel, OutboxMessage]):
    """Outbox платежей: `add` - из бизнес-логики (IOutboxRepository), остальное - для relay."""

    model = OutboxEventDBModel

    async def add(self, event: PaymentCreated) -> None:
        await self._save(
            OutboxEventDBModel(
                routing_key=PAYMENT_CREATED_ROUTING_KEY,
                payload={"payment_id": str(event.payment_id)},
            )
        )

    async def get_unpublished_for_update(self, limit: int) -> list[OutboxMessage]:
        """Неотправленные события по порядку создания, `FOR UPDATE SKIP LOCKED`."""
        return await self._get_many_by_specs(
            [UnpublishedOutboxSpec(), LockedOutboxBatchSpec(limit)]
        )

    async def mark_published(self, ids: list[UUID]) -> None:
        """Проставляет `published_at` отправленным событиям."""
        query = update(self.model).values(published_at=func.now())
        await self._execute(self._apply_specs(query=query, specs=[OutboxByIdsSpec(ids)]))
