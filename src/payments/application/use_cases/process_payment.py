from dataclasses import dataclass
from uuid import UUID

from src.payments.domain.entities import Payment
from src.payments.domain.exceptions import PaymentNotFoundError
from src.payments.domain.interfaces.gateway import IPaymentGateway
from src.payments.domain.interfaces.unit_of_work import IPaymentsUnitOfWork
from src.payments.domain.interfaces.webhook import IWebhookSender
from src.payments.domain.value_objects import PaymentStatus


@dataclass(frozen=True, slots=True)
class ProcessPaymentInputDTO:
    payment_id: UUID


@dataclass(frozen=True, slots=True)
class ProcessPaymentOutputDTO:
    payment_id: UUID
    status: PaymentStatus


class ProcessPaymentUseCase:
    """Обработка платежа: шлюз → статус → webhook; обработанный платёж повторно не проводится."""

    def __init__(
        self,
        uow: IPaymentsUnitOfWork,
        gateway: IPaymentGateway,
        webhook_sender: IWebhookSender,
    ) -> None:
        self._uow = uow
        self._gateway = gateway
        self._webhook_sender = webhook_sender

    async def execute(self, input_dto: ProcessPaymentInputDTO) -> ProcessPaymentOutputDTO:
        async with self._uow:
            payment = await self._get_payment(input_dto.payment_id)

        if payment.status is PaymentStatus.PENDING:
            payment = await self._process(payment)

        await self._webhook_sender.send(payment)
        return ProcessPaymentOutputDTO(payment_id=payment.id, status=payment.status)

    async def _process(self, payment: Payment) -> Payment:
        if await self._gateway.charge(payment):
            payment.mark_succeeded()
        else:
            payment.mark_failed()

        async with self._uow:
            if await self._uow.payments.save_processing_result(payment):
                await self._uow.commit()
                return payment
            return await self._get_payment(payment.id)

    async def _get_payment(self, payment_id: UUID) -> Payment:
        payment = await self._uow.payments.get_by_id(payment_id)
        if payment is None:
            raise PaymentNotFoundError(payment_id=payment_id)
        return payment
