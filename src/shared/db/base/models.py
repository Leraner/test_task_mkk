from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import DateTime, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseDBModel(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy-моделей.

    `id` — UUIDv7: глобально уникален и упорядочен по времени создания,
    поэтому подходит и для сортировки в порядке вставки (например, outbox).
    """

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid7)

    def to_entity(self):
        raise NotImplementedError("to_entity method not implemented in base class")


class Timestamp:
    """Миксин с полями created_at и updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
