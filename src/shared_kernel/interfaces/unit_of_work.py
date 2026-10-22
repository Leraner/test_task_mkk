from types import TracebackType
from typing import Protocol, Self


class IUnitOfWork(Protocol):
    async def __aenter__(self) -> Self:
        """Начинает блок работы с транзакцией."""
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Откатывает всё, что не было зафиксировано через `commit()`."""
        ...

    async def commit(self) -> None:
        """Фиксирует все изменения, сделанные репозиториями в текущей транзакции."""
        ...

    async def rollback(self) -> None:
        """Откатывает все незафиксированные изменения текущей транзакции."""
        ...
