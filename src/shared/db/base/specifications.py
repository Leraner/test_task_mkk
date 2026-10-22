from typing import Any, Protocol, TypeAlias, TypeVar

from sqlalchemy import Delete, Select, Update

from src.shared.db.base.models import BaseDBModel

QueryType: TypeAlias = Select[Any] | Update | Delete
T = TypeVar("T", bound=BaseDBModel)


class Specification[T](Protocol):
    """Контракт для фильтрации запросов. Реализации применяют условие к SQLAlchemy query."""

    def apply(self, query: QueryType, model: type[T]) -> QueryType: ...
