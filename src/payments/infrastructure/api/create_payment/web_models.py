import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import Field, HttpUrl

from src.payments.application.use_cases.create_payment import CreatePaymentInputDTO
from src.payments.domain.value_objects import Currency, PaymentStatus
from src.shared.web.web_models import BaseResponseDataModel, BaseWebInputModel


class CreatePaymentInputModel(BaseWebInputModel):
    amount: Decimal = Field(gt=0, decimal_places=2)
    currency: Currency
    description: str = Field(max_length=255)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl

    def as_dto(self, idempotency_key: str) -> CreatePaymentInputDTO:
        return CreatePaymentInputDTO(
            idempotency_key=idempotency_key,
            idempotency_fingerprint=self._idempotency_fingerprint(),
            amount=self.amount,
            currency=self.currency,
            description=self.description,
            webhook_url=str(self.webhook_url),
            metadata=self.metadata,
        )

    def _idempotency_fingerprint(self) -> str:
        """SHA-256 канонизированного тела запроса (idempotency fingerprint).

        Ключи сортируются, сумма приводится к 2 знакам - иначе равные запросы
        (`{"a":1,"b":2}` / `{"b":2,"a":1}`, `100` / `100.00`) дали бы разный хэш.
        """
        payload = json.dumps(
            {
                "amount": f"{self.amount:.2f}",
                "currency": self.currency,
                "description": self.description,
                "webhook_url": str(self.webhook_url),
                "metadata": self.metadata,
            },
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode()).hexdigest()


class CreatePaymentResponseDataModel(BaseResponseDataModel):
    payment_id: UUID
    status: PaymentStatus
    created_at: datetime
