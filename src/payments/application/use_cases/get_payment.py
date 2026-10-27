from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.payments.domain.exceptions import PaymentNotFoundError
from src.payments.domain.interfaces.repository import IPaymentsRepository
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
    created_at: datetime
    processed_at: datetime | None


class GetPaymentUseCase:
    """
    Получение платежа по id через репозиторий: только чтение, UoW не нужен.

    Если платежа нет - `PaymentNotFoundError` (→ 404 через exception_map).
    """

    def __init__(self, payments: IPaymentsRepository) -> None:
        self._payments = payments

    async def execute(self, input_dto: GetPaymentInputDTO) -> GetPaymentOutputDTO:
        payment = await self._payments.get_by_id(input_dto.payment_id)
        if payment is None:
            raise PaymentNotFoundError(payment_id=input_dto.payment_id)

        return GetPaymentOutputDTO(
            payment_id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            metadata=payment.metadata,
            status=payment.status,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )
