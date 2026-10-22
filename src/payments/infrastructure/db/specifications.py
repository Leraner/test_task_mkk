from dataclasses import dataclass
from uuid import UUID

from src.payments.infrastructure.db.models import PaymentDBModel
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
