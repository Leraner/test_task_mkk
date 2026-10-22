from src.payments.application.use_cases.create_payment import CreatePaymentOutputDTO
from src.payments.infrastructure.api.create_payment.web_models import (
    CreatePaymentResponseDataModel,
)


class CreatePaymentPresenter:
    @staticmethod
    def present(dto: CreatePaymentOutputDTO) -> CreatePaymentResponseDataModel:
        return CreatePaymentResponseDataModel(
            payment_id=dto.payment_id,
            status=dto.status,
            created_at=dto.created_at,
        )
