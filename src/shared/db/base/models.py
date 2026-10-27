from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid7

from sqlalchemy import DateTime, MetaData, Uuid, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Предсказуемые имена ограничений и индексов вместо сгенерированных БД -
# чтобы миграции (Alembic) могли ссылаться на них по имени.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class BaseDBModel(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy-моделей.

    `id` - UUIDv7: глобально уникален и упорядочен по времени создания,
    поэтому подходит и для сортировки в порядке вставки (например, outbox).
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)

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
