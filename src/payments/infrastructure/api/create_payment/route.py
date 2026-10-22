from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Header
from starlette import status

from src.payments.application.use_cases.create_payment import CreatePaymentUseCase
from src.payments.infrastructure.api.create_payment.presenter import (
    CreatePaymentPresenter,
)
from src.payments.infrastructure.api.create_payment.web_models import (
    CreatePaymentInputModel,
    CreatePaymentResponseDataModel,
)
from src.shared.web.web_models import BaseWebOutputModel

router = APIRouter()


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
@inject
async def create_payment(
    body: CreatePaymentInputModel,
    idempotency_key: Annotated[str, Header(alias="Idempotency-Key", min_length=1, max_length=255)],
    use_case: FromDishka[CreatePaymentUseCase],
    presenter: FromDishka[CreatePaymentPresenter],
) -> BaseWebOutputModel[CreatePaymentResponseDataModel]:
    uc_output = await use_case.execute(body.as_dto(idempotency_key))
    response_data = presenter.present(uc_output)
    return response_data.as_web_output()
