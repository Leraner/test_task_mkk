from dataclasses import dataclass
from typing import Any, Protocol
from uuid import UUID

from src.payments.domain.events import PaymentCreated


@dataclass(frozen=True, slots=True)
class OutboxMessage:
    """Неотправленное событие из outbox: с каким `routing_key` и что (`payload`) публиковать."""

    id: UUID
    routing_key: str
    payload: dict[str, Any]


class IOutboxRepository(Protocol):
    async def add(self, event: PaymentCreated) -> None:
        """Сохраняет событие в outbox в текущей транзакции для последующей публикации."""
        ...

    async def get_unpublished_for_update(self, limit: int) -> list[OutboxMessage]:
        """Возвращает до `limit` неотправленных событий, блокируя их до конца транзакции."""
        ...

    async def mark_published(self, ids: list[UUID]) -> None:
        """Помечает события отправленными."""
        ...
