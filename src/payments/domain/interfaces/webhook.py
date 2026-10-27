from typing import Protocol

from src.payments.domain.entities import Payment


class IWebhookSender(Protocol):
    async def send(self, payment: Payment) -> None:
        """Одна попытка уведомить клиента: WebhookDeliveryError или WebhookRejectedError."""
        ...
