import httpx

from src.payments.domain.entities import Payment
from src.payments.domain.exceptions import WebhookDeliveryError, WebhookRejectedError

# Кроме 5xx, повтор поможет при таймауте запроса и rate limit.
RETRYABLE_STATUS_CODES = frozenset({408, 429})


class HttpWebhookSender:
    """POST результата платежа на `webhook_url`, одна попытка; повторы делает consumer."""

    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def send(self, payment: Payment) -> None:
        payload = {
            "payment_id": str(payment.id),
            "status": payment.status,
            "amount": str(payment.amount),
            "currency": payment.currency,
            "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
        }
        try:
            response = await self._client.post(payment.webhook_url, json=payload)
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            status_code = err.response.status_code
            if status_code >= 500 or status_code in RETRYABLE_STATUS_CODES:
                raise WebhookDeliveryError(payment_id=str(payment.id), reason=repr(err)) from err
            raise WebhookRejectedError(payment_id=str(payment.id), reason=repr(err)) from err
        except httpx.TransportError as err:
            raise WebhookDeliveryError(payment_id=str(payment.id), reason=repr(err)) from err
