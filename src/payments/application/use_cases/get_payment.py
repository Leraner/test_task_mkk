from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.payments.domain.interfaces.unit_of_work import IPaymentsUnitOfWork
from src.payments.domain.value_objects import Currency, PaymentStatus


@dataclass(frozen=True, slots=True)
class GetPaymentInputDTO:
    payment_id: UUID


@dataclass(frozen=True, slots=True)
class GetPaymentOutputDTO:
    payment_id: UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any]
    status: PaymentStatus
    idempotency_key: str
    webhook_url: str
    created_at: datetime
    processed_at: datetime | None


class GetPaymentUseCase:
    """
    Получение платежа по id через `uow.payments` внутри `async with self._uow:`.

    Если платежа нет — `PaymentNotFoundError` (→ 404 через exception_map).
    """

    def __init__(self, uow: IPaymentsUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: GetPaymentInputDTO) -> GetPaymentOutputDTO:
        raise NotImplementedError
