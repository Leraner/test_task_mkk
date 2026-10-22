from uuid import UUID

from src.payments.domain.entities import Payment
from src.payments.domain.events import PaymentCreated
from src.payments.domain.exceptions import (
    PaymentAlreadyExistsError,
    PaymentNotFoundError,
)
from src.payments.infrastructure.db.models import (
    IDEMPOTENCY_KEY_CONSTRAINT,
    OutboxEventDBModel,
    PaymentDBModel,
)
from src.payments.infrastructure.db.specifications import (
    PaymentByIdempotencyKeySpec,
    PaymentByIdSpec,
)
from src.shared.db.base.repository import BaseRepository
from src.shared.db.exceptions import DatabaseError

PAYMENTS_NEW_TOPIC = "payments.new"


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


class OutboxRepository(BaseRepository[OutboxEventDBModel, None]):
    """Пишет события платежей в outbox; читает его паблишер, не этот репозиторий."""

    model = OutboxEventDBModel

    async def add(self, event: PaymentCreated) -> None:
        await self._save(
            OutboxEventDBModel(
                topic=PAYMENTS_NEW_TOPIC,
                payload={"payment_id": str(event.payment_id)},
            )
        )
