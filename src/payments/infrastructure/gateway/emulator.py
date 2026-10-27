import asyncio
import random

from src.payments.domain.entities import Payment

MIN_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 5.0
SUCCESS_RATE = 0.9


class PaymentGatewayEmulator:
    """Эмуляция внешнего платёжного шлюза по ТЗ: отвечает за 2-5 с, 90% платежей проходят."""

    async def charge(self, payment: Payment) -> bool:
        await asyncio.sleep(random.uniform(MIN_DELAY_SECONDS, MAX_DELAY_SECONDS))
        return random.random() < SUCCESS_RATE
