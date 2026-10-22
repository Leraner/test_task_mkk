from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from src.payments.domain.value_objects import Currency, PaymentStatus
from src.shared.web.web_models import BaseResponseDataModel


class PaymentResponseDataModel(BaseResponseDataModel):
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
