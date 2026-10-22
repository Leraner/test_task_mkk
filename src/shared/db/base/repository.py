from typing import Any, ClassVar, cast

from sqlalchemy import delete as sa_delete
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.db.base.models import BaseDBModel
from src.shared.db.base.specifications import QueryType, Specification
from src.shared.db.exceptions import DatabaseError


class BaseRepository[T: BaseDBModel, E]:
    """Базовый репозиторий с общими CRUD-операциями поверх SQLAlchemy.

    ``T`` — ORM-модель, ``E`` — доменная сущность, которую возвращает ``to_entity()`` для этой модели.
    Наследники задают ``model`` и добавляют публичные методы.

    Репозиторий не управляет транзакцией: он только добавляет изменения в сессию
    и делает flush. Commit/rollback — ответственность ``IUnitOfWork``, поэтому
    несколько репозиториев на одной сессии пишут в одну транзакцию.
    При IntegrityError бросает DatabaseError; откат делает тот, кто владеет транзакцией.
    """

    model: ClassVar[type[BaseDBModel]]

    def __init__(self, db_session: AsyncSession):
        self._session = db_session

    async def _get_one_by_specs(
        self,
        specs: list[Specification[T]],
    ) -> E | None:
        """Возвращает одну запись по спецификациям или None."""
        query = select(self.model)
        query = self._apply_specs(query=query, specs=specs)

        result = await self._execute(query=query)
        result_model = result.scalars().unique().one_or_none()
        return cast(E, result_model.to_entity()) if result_model else None

    async def _get_many_by_specs(
        self,
        specs: list[Specification[T]],
    ) -> list[E]:
        """Возвращает список записей по спецификациям."""
        query = select(self.model)
        query = self._apply_specs(query=query, specs=specs)

        result = await self._execute(query=query)
        result_models = result.scalars().unique().all()
        return [cast(E, result_model.to_entity()) for result_model in result_models]

    async def _get_total_count_with_specs(
        self,
        specs: list[Specification[T]],
    ) -> int:
        """Возвращает количество записей по спецификациям."""
        query = select(func.count(self.model.id))
        query = self._apply_specs(query=query, specs=specs)
        result = await self._execute(query=query)
        return result.scalar_one()

    async def _delete_by_specs(
        self,
        specs: list[Specification[T]],
    ) -> None:
        """Удаляет записи по спецификациям."""
        query = sa_delete(self.model)
        query = self._apply_specs(query=query, specs=specs)
        await self._execute(query=query)

    def _apply_specs(
        self,
        query: QueryType,
        specs: list[Specification[T]],
    ) -> QueryType:
        """Последовательно применяет спецификации к запросу."""
        for spec in specs:
            query = spec.apply(query=query, model=cast(type[T], self.model))
        return query

    async def _execute(
        self,
        query: QueryType,
    ) -> Any:
        """Выполняет запрос. При IntegrityError — DatabaseError."""
        try:
            return await self._session.execute(query)
        except IntegrityError as err:
            raise self.__integrity_error(err) from err

    async def _save_all(self, objects: list[T]) -> None:
        """Добавляет список объектов в транзакцию без возврата обновлённых данных."""
        await self.__save(objects=objects, refresh=False)

    async def _save_all_with_return(self, objects: list[T]) -> list[E]:
        """Добавляет список объектов в транзакцию и возвращает их как доменные сущности."""
        await self.__save(objects=objects, refresh=True)
        return [cast(E, obj.to_entity()) for obj in objects]

    async def _save(self, obj: T) -> None:
        """Добавляет один объект в транзакцию без возврата обновлённых данных."""
        await self.__save(objects=[obj], refresh=False)

    async def _save_with_return(self, obj: T) -> E:
        """Добавляет объект в транзакцию и возвращает его как доменную сущность (с полями из БД)."""
        await self.__save(objects=[obj], refresh=True)
        return cast(E, obj.to_entity())

    async def __save(self, objects: list[T], refresh: bool) -> None:
        """add + flush; при ``refresh`` перечитывает объекты, чтобы получить auto-generated поля.

        Flush нужен, чтобы ошибки ограничений всплыли сразу здесь, а не на commit в UoW.
        """
        self._session.add_all(objects)
        await self._flush()

        if refresh:
            for obj in objects:
                await self._session.refresh(obj)

    async def _delete(self, obj: T) -> None:
        """Помечает объект на удаление в рамках транзакции."""
        await self._session.delete(obj)
        await self._flush()

    async def _flush(self) -> None:
        """Flush с обработкой IntegrityError."""
        try:
            await self._session.flush()
        except IntegrityError as err:
            raise self.__integrity_error(err) from err

    def _copy_columns(
        self,
        existing: T,
        fresh: T,
        exclude: tuple[str, ...] = ("id", "created_at", "updated_at"),
    ) -> None:
        """Копирует значения колонок из ``fresh`` в отслеживаемый сессией ``existing``.

        Нужно для update(): нельзя просто заменить объект в сессии на ``fresh``
        (SQLAlchemy не свяжет его с существующей строкой), поэтому переносим
        значения полей на уже отслеживаемый инстанс. ``fresh`` обычно строится
        через ``Model.from_entity()`` — так список полей не дублируется отдельно
        в update(), а берётся из единственного источника истины.
        """
        for column in self.model.__table__.columns:
            if column.key in exclude:
                continue
            setattr(existing, column.key, getattr(fresh, column.key))

    @staticmethod
    def __integrity_error(err: IntegrityError) -> DatabaseError:
        """Оборачивает IntegrityError в DatabaseError инфраструктурного слоя."""
        return DatabaseError(
            detail="Database query execution failed",
            ru_detail="Ошибка при выполнении запроса к базе данных",
            original_error=err,
        )
