from collections.abc import AsyncIterator

import httpx
from dishka import Provider, Scope, provide

from src.payments.application.use_cases.process_payment import ProcessPaymentUseCase
from src.payments.domain.interfaces.gateway import IPaymentGateway
from src.payments.domain.interfaces.unit_of_work import IPaymentsUnitOfWork
from src.payments.domain.interfaces.webhook import IWebhookSender
from src.payments.infrastructure.db.unit_of_work import PaymentsUnitOfWork
from src.payments.infrastructure.gateway.emulator import PaymentGatewayEmulator
from src.payments.infrastructure.webhook.sender import HttpWebhookSender
from src.payments.infrastructure.webhook.settings import WebhookSettings, get_webhook_settings


class ConsumerProvider(Provider):
    scope = Scope.REQUEST

    unit_of_work = provide(PaymentsUnitOfWork, provides=IPaymentsUnitOfWork)
    gateway = provide(PaymentGatewayEmulator, provides=IPaymentGateway, scope=Scope.APP)
    webhook_sender = provide(HttpWebhookSender, provides=IWebhookSender, scope=Scope.APP)
    use_case = provide(ProcessPaymentUseCase)

    @provide(scope=Scope.APP)
    def get_webhook_settings(self) -> WebhookSettings:
        return get_webhook_settings()

    @provide(scope=Scope.APP)
    async def get_http_client(self, settings: WebhookSettings) -> AsyncIterator[httpx.AsyncClient]:
        """Один клиент (пул соединений) на процесс; закрывается вместе с контейнером."""
        async with httpx.AsyncClient(timeout=settings.timeout) as client:
            yield client
