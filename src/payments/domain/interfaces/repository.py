from typing import Protocol
from uuid import UUID

from src.payments.domain.entities import Payment


class IPaymentsRepository(Protocol):
    async def get_by_id(self, payment_id: UUID) -> Payment | None:
        """Возвращает платёж по id или None, если его нет."""
        ...

    async def get_by_idempotency_key(self, idempotency_key: str) -> Payment:
        """Возвращает платёж по ключу идемпотентности; если его нет — PaymentNotFoundError."""
        ...

    async def add(self, payment: Payment) -> Payment:
        """Сохраняет новый платёж и возвращает его с полями из БД (created_at).

        Если ключ идемпотентности занят — PaymentAlreadyExistsError.
        """
        ...
