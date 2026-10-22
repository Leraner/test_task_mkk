from src.payments.application.use_cases.get_payment import GetPaymentOutputDTO
from src.payments.infrastructure.api.get_payment.web_models import PaymentResponseDataModel


class GetPaymentPresenter:
    @staticmethod
    def present(dto: GetPaymentOutputDTO) -> PaymentResponseDataModel:
        return PaymentResponseDataModel(
            payment_id=dto.payment_id,
            amount=dto.amount,
            currency=dto.currency,
            description=dto.description,
            metadata=dto.metadata,
            status=dto.status,
            idempotency_key=dto.idempotency_key,
            webhook_url=dto.webhook_url,
            created_at=dto.created_at,
            processed_at=dto.processed_at,
        )
