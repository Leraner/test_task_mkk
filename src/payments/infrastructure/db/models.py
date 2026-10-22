from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Enum, Index, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.payments.domain.entities import Payment
from src.payments.domain.value_objects import Currency, PaymentStatus
from src.shared.db.base.models import BaseDBModel, Timestamp

IDEMPOTENCY_KEY_CONSTRAINT = "uq_payments_idempotency_key"


class PaymentDBModel(Timestamp, BaseDBModel):
    __tablename__ = "payments"

    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency"),
    )
    description: Mapped[str] = mapped_column(String(255))
    payment_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default="{}")
    status: Mapped[PaymentStatus] = mapped_column(Enum(PaymentStatus, name="payment_status"))
    idempotency_key: Mapped[str] = mapped_column(String(255))
    webhook_url: Mapped[str] = mapped_column(String(2048))
    idempotency_fingerprint: Mapped[str] = mapped_column(String(64))
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (UniqueConstraint("idempotency_key", name=IDEMPOTENCY_KEY_CONSTRAINT),)

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
            idempotency_fingerprint=payment.idempotency_fingerprint,
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
            idempotency_fingerprint=self.idempotency_fingerprint,
            created_at=self.created_at,
            processed_at=self.processed_at,
        )


class OutboxEventDBModel(BaseDBModel):
    """Transactional outbox: событие пишется в одной транзакции с платежом.

    Паблишер выбирает строки с `published_at IS NULL` в порядке `id` (UUIDv7 — по времени
    создания), отправляет `payload` в `topic` и проставляет `published_at`.
    """

    __tablename__ = "outbox"

    topic: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "ix_outbox_unpublished",
            "id",
            postgresql_where=published_at.is_(None),
        ),
    )
