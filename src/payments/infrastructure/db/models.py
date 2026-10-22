from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Enum, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.payments.domain.entities import Payment
from src.payments.domain.value_objects import Currency, PaymentStatus
from src.shared.db.base.models import BaseDBModel, Timestamp


class PaymentDBModel(Timestamp, BaseDBModel):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency"),
    )
    description: Mapped[str] = mapped_column(String(255))
    payment_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"))
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True)
    webhook_url: Mapped[str] = mapped_column(String(2048))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    @classmethod
    def from_entity(cls, payment: Payment) -> PaymentDBModel:
        return cls(
            id=payment.id,
            amount=payment.amount,
            currency=payment.currency,
            description=payment.description,
            payment_metadata=payment.metadata,
            status=payment.status,
            idempotency_key=payment.idempotency_key,
            webhook_url=payment.webhook_url,
            created_at=payment.created_at,
            processed_at=payment.processed_at,
        )

    def to_entity(self) -> Payment:
        return Payment(
            id=self.id,
            amount=self.amount,
            currency=self.currency,
            description=self.description,
            metadata=self.payment_metadata,
            status=self.status,
            idempotency_key=self.idempotency_key,
            webhook_url=self.webhook_url,
            created_at=self.created_at,
            processed_at=self.processed_at,
        )
