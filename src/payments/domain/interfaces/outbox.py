from typing import Protocol

from src.payments.domain.events import PaymentCreated


class IOutboxRepository(Protocol):
    async def add(self, event: PaymentCreated) -> None:
        """Сохраняет событие в outbox в текущей транзакции для последующей публикации."""
        ...
