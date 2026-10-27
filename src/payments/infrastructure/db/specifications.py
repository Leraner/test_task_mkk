from dataclasses import dataclass
from uuid import UUID

from src.payments.domain.value_objects import PaymentStatus
from src.payments.infrastructure.db.models import OutboxEventDBModel, PaymentDBModel
from src.shared.db.base.specifications import QueryType


@dataclass(frozen=True, slots=True)
class PaymentByIdSpec:
    payment_id: UUID

    def apply(self, query: QueryType, model: type[PaymentDBModel]) -> QueryType:
        return query.where(model.id == self.payment_id)


@dataclass(frozen=True, slots=True)
class PaymentByIdempotencyKeySpec:
    idempotency_key: str

    def apply(self, query: QueryType, model: type[PaymentDBModel]) -> QueryType:
        return query.where(model.idempotency_key == self.idempotency_key)


@dataclass(frozen=True, slots=True)
class PendingPaymentSpec:
    def apply(self, query: QueryType, model: type[PaymentDBModel]) -> QueryType:
        return query.where(model.status == PaymentStatus.PENDING)


@dataclass(frozen=True, slots=True)
class UnpublishedOutboxSpec:
    def apply(self, query: QueryType, model: type[OutboxEventDBModel]) -> QueryType:
        return query.where(model.published_at.is_(None))


@dataclass(frozen=True, slots=True)
class OutboxByIdsSpec:
    ids: list[UUID]

    def apply(self, query: QueryType, model: type[OutboxEventDBModel]) -> QueryType:
        return query.where(model.id.in_(self.ids))


@dataclass(frozen=True, slots=True)
class LockedOutboxBatchSpec:
    """Первые `limit` строк по `id` под `FOR UPDATE SKIP LOCKED` - только для SELECT."""

    limit: int

    def apply(self, query: QueryType, model: type[OutboxEventDBModel]) -> QueryType:
        return query.order_by(model.id).limit(self.limit).with_for_update(skip_locked=True)
