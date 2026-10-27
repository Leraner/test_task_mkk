from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.payments.domain.entities import Payment
from src.payments.domain.events import PaymentCreated
from src.payments.domain.exceptions import IdempotencyKeyReusedError, PaymentAlreadyExistsError
from src.payments.domain.interfaces.unit_of_work import IPaymentsUnitOfWork
from src.payments.domain.value_objects import Currency, PaymentStatus


@dataclass(frozen=True, slots=True)
class CreatePaymentInputDTO:
    idempotency_key: str
    idempotency_fingerprint: str
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
    """Создание платежа: insert-first по idempotency_key, событие в outbox - в той же транзакции."""

    def __init__(self, uow: IPaymentsUnitOfWork) -> None:
        self._uow = uow

    async def execute(self, input_dto: CreatePaymentInputDTO) -> CreatePaymentOutputDTO:
        new_payment = Payment(
            amount=input_dto.amount,
            currency=input_dto.currency,
            description=input_dto.description,
            idempotency_key=input_dto.idempotency_key,
            webhook_url=input_dto.webhook_url,
            idempotency_fingerprint=input_dto.idempotency_fingerprint,
            metadata=input_dto.metadata,
        )

        async with self._uow:
            try:
                payment = await self._uow.payments.add(new_payment)
            except PaymentAlreadyExistsError:
                await self._uow.rollback()
                payment = await self._uow.payments.get_by_idempotency_key(input_dto.idempotency_key)
                if payment.idempotency_fingerprint != new_payment.idempotency_fingerprint:
                    raise IdempotencyKeyReusedError(idempotency_key=input_dto.idempotency_key)
            else:
                await self._uow.outbox.add(PaymentCreated(payment_id=payment.id))
                await self._uow.commit()

        return CreatePaymentOutputDTO(
            payment_id=payment.id,
            status=payment.status,
            created_at=payment.created_at,
        )
