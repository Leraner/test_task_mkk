from types import TracebackType
from typing import Self

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.exceptions import DatabaseError


class SqlAlchemyUnitOfWork:
    """
    Базовый UoW поверх `AsyncSession`.

    Сессией владеет DI-scope (запрос / сообщение): он открывает и закрывает её.
    UoW задаёт границу транзакции: `async with uow:` откатывает на выходе всё,
    что не зафиксировано через `commit()`. UoW конкретного bounded context
    наследуется от этого класса и создаёт свои репозитории в `__init__`.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.rollback()

    async def commit(self) -> None:
        try:
            await self._session.commit()
        except IntegrityError as err:
            await self._session.rollback()
            raise DatabaseError(
                detail="Database transaction commit failed",
                ru_detail="Ошибка при фиксации транзакции в базе данных",
                original_error=err,
            ) from err

    async def rollback(self) -> None:
        await self._session.rollback()
