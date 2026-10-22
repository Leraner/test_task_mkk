from uuid import UUID

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

from src.payments.application.use_cases.get_payment import (
    GetPaymentInputDTO,
    GetPaymentUseCase,
)
from src.payments.infrastructure.api.get_payment.presenter import GetPaymentPresenter
from src.payments.infrastructure.api.get_payment.web_models import (
    PaymentResponseDataModel,
)
from src.shared.web.web_models import BaseWebOutputModel

router = APIRouter()


@router.get("/{payment_id}")
@inject
async def get_payment(
    payment_id: UUID,
    use_case: FromDishka[GetPaymentUseCase],
) -> BaseWebOutputModel[PaymentResponseDataModel]:
    output = await use_case.execute(GetPaymentInputDTO(payment_id=payment_id))
    return GetPaymentPresenter.present(output).as_web_output()
