from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class BaseDBModel(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy-моделей."""

    id: Mapped[int] = mapped_column(primary_key=True, nullable=False)

    def to_entity(self):
        raise NotImplementedError("to_entity method not implemented in base class")


class Timestamp:
    """Миксин с полями created_at и updated_at."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
