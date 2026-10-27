from typing import Protocol

from src.payments.domain.entities import Payment


class IPaymentGateway(Protocol):
    async def charge(self, payment: Payment) -> bool:
        """Проводит платёж через внешний шлюз: True - платёж прошёл, False - шлюз отказал."""
        ...
