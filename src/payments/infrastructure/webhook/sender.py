import asyncio
import ipaddress
import socket
from urllib.parse import urlsplit

import httpx

from src.payments.domain.entities import Payment
from src.payments.domain.exceptions import WebhookDeliveryError, WebhookRejectedError
from src.payments.infrastructure.webhook.settings import WebhookSettings

# Кроме 5xx, повтор поможет при таймауте запроса и rate limit.
RETRYABLE_STATUS_CODES = frozenset({408, 429})


class HttpWebhookSender:
    """POST результата платежа на webhook_url, одна попытка; повторы делает consumer."""

    def __init__(self, client: httpx.AsyncClient, settings: WebhookSettings) -> None:
        self._client = client
        self._settings = settings

    async def send(self, payment: Payment) -> None:
        payment_id = str(payment.id)
        if not self._settings.allow_private_networks:
            await self._ensure_public_host(payment.webhook_url, payment_id)

        payload = {
            "payment_id": payment_id,
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
                raise WebhookDeliveryError(payment_id=payment_id, reason=repr(err)) from err
            raise WebhookRejectedError(payment_id=payment_id, reason=repr(err)) from err
        except httpx.TransportError as err:
            raise WebhookDeliveryError(payment_id=payment_id, reason=repr(err)) from err

    @staticmethod
    async def _ensure_public_host(url: str, payment_id: str) -> None:
        """Защита от SSRF: webhook не уходит во внутреннюю сеть (БД, брокер, метаданные облака).
        Редиректы httpx не выполняет, поэтому достаточно проверить сам URL."""
        parts = urlsplit(url)
        port = parts.port or (443 if parts.scheme == "https" else 80)
        try:
            infos = await asyncio.get_running_loop().getaddrinfo(
                parts.hostname, port, type=socket.SOCK_STREAM
            )
        except OSError as err:
            raise WebhookDeliveryError(payment_id=payment_id, reason=repr(err)) from err

        for *_, sockaddr in infos:
            address = ipaddress.ip_address(sockaddr[0])
            if not address.is_global:
                raise WebhookRejectedError(
                    payment_id=payment_id,
                    reason=f"{parts.hostname} resolves to non-public address {address}",
                )
