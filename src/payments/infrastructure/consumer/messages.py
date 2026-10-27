from uuid import UUID

from pydantic import BaseModel

from src.payments.application.use_cases.process_payment import ProcessPaymentInputDTO


class PaymentCreatedMessage(BaseModel):
    """Тело события `payment.created`, которое публикует outbox relay."""

    payment_id: UUID

    def to_dto(self) -> ProcessPaymentInputDTO:
        return ProcessPaymentInputDTO(payment_id=self.payment_id)
