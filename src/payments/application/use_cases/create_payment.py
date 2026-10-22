from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.payments.domain.interfaces.unit_of_work import IPaymentsUnitOfWork
from src.payments.domain.value_objects import Currency, PaymentStatus


@dataclass(frozen=True, slots=True)
class CreatePaymentInputDTO:
    idempotency_key: str
    amount: Decimal
    currency: Currency
    description: str
    webhook_url: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CreatePaymentOutputDTO:
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime


class CreatePaymentUseCase:
    """
    Создание платежа. Всё выполняется внутри `async with self._uow:`.

    1. Если платёж с таким `idempotency_key` уже есть — вернуть его (повторный запрос).
    2. Иначе создать `Payment` в статусе pending.
    3. В одной транзакции с платежом записать событие `payments.new` в outbox.
    4. Зафиксировать платёж и событие одним `uow.commit()`.
    """

    def __init__(self, uow: IPaymentsUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, dto: CreatePaymentInputDTO) -> CreatePaymentOutputDTO:
        raise NotImplementedError
