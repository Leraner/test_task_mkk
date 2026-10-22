from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Index, String, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.shared.db.base.models import BaseDBModel


class OutboxEventDBModel(BaseDBModel):
    """Общая таблица transactional outbox для всех bounded contexts.

    Событие пишется в одной транзакции с изменением агрегата; паблишер выбирает строки
    с `published_at IS NULL` в порядке `id` (UUIDv7 — по времени создания), отправляет
    `payload` в `topic` и проставляет `published_at`. `id` же служит идентификатором события.
    """

    __tablename__ = "outbox_events"

    aggregate_type: Mapped[str] = mapped_column(String(50))
    aggregate_id: Mapped[UUID] = mapped_column(Uuid)
    event_type: Mapped[str] = mapped_column(String(100))
    topic: Mapped[str] = mapped_column(String(255))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        Index(
            "outbox_events_unpublished_idx",
            "id",
            postgresql_where=published_at.is_(None),
        ),
    )
