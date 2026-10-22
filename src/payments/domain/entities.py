from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID, uuid7

from src.payments.domain.exceptions import (
    InvalidIdempotencyKeyError,
    InvalidPaymentAmountError,
    InvalidWebhookUrlError,
    PaymentAlreadyProcessedError,
)
from src.payments.domain.value_objects import Currency, PaymentStatus


class Payment:
    def __init__(
        self,
        *,
        id: UUID | None = None,
        amount: Decimal,
        currency: Currency,
        description: str,
        idempotency_key: str,
        webhook_url: str,
        idempotency_fingerprint: str,
        status: PaymentStatus = PaymentStatus.PENDING,
        metadata: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        processed_at: datetime | None = None,
    ) -> None:
        self.id = id or uuid7()
        self.amount = self._validate_amount(amount)
        self.currency = currency
        self.description = description
        self.idempotency_key = self._validate_idempotency_key(idempotency_key)
        self.webhook_url = self._validate_webhook_url(webhook_url)
        self.idempotency_fingerprint = idempotency_fingerprint
        self.metadata = metadata or {}
        self._status = status
        self.created_at = created_at
        self._processed_at = processed_at

    @property
    def status(self) -> PaymentStatus:
        return self._status

    @property
    def processed_at(self) -> datetime | None:
        return self._processed_at

    def mark_succeeded(self) -> None:
        self._finish(PaymentStatus.SUCCEEDED)

    def mark_failed(self) -> None:
        self._finish(PaymentStatus.FAILED)

    def _finish(self, status: PaymentStatus) -> None:
        if self._status is not PaymentStatus.PENDING:
            raise PaymentAlreadyProcessedError(payment_id=self.id, status=self._status)
        self._status = status
        self._processed_at = datetime.now(UTC)

    @staticmethod
    def _validate_amount(amount: Decimal) -> Decimal:
        exponent = amount.as_tuple().exponent
        if not amount.is_finite() or amount <= 0 or (isinstance(exponent, int) and exponent < -2):
            raise InvalidPaymentAmountError(amount=str(amount))
        return amount

    @staticmethod
    def _validate_idempotency_key(idempotency_key: str) -> str:
        if not idempotency_key.strip():
            raise InvalidIdempotencyKeyError()
        return idempotency_key

    @staticmethod
    def _validate_webhook_url(webhook_url: str) -> str:
        parts = urlsplit(webhook_url)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise InvalidWebhookUrlError(webhook_url=webhook_url)
        return webhook_url

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Payment):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    def __repr__(self) -> str:
        return f"Payment(id={self.id!r}, status={self._status!r})"
