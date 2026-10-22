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
    При IntegrityError делает rollback и бросает DatabaseError.
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
        await self._commit()

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
        """Выполняет запрос. При IntegrityError — rollback + DatabaseError."""
        try:
            return await self._session.execute(query)
        except IntegrityError as err:
            await self.__handle_integrity_error(err)

    async def _save_all(self, objects: list[T]) -> None:
        """Сохраняет список объектов без возврата обновлённых данных."""
        await self.__save_without_refresh(objects=objects)

    async def _save_all_with_return(self, objects: list[T]) -> list[E]:
        """Сохраняет список объектов и возвращает их как доменные сущности."""
        await self.__save_with_refresh(objects=objects)
        return [cast(E, obj.to_entity()) for obj in objects]

    async def _save(self, obj: T) -> None:
        """Сохраняет один объект без возврата обновлённых данных."""
        await self.__save_without_refresh(objects=[obj])

    async def _save_with_return(self, obj: T) -> E:
        """Сохраняет объект и возвращает его как доменную сущность (с обновлёнными полями из БД)."""
        await self.__save_with_refresh(objects=[obj])
        return cast(E, obj.to_entity())

    async def __save_without_refresh(self, objects: list[T]) -> None:
        for obj in objects:
            self._session.add(obj)

        try:
            await self._session.commit()
        except IntegrityError as err:
            await self.__handle_integrity_error(err)

    async def __save_with_refresh(self, objects: list[T]) -> None:
        """flush + refresh каждого объекта + commit. Нужен для получения auto-generated полей."""
        for obj in objects:
            self._session.add(obj)

        try:
            await self._session.flush()

            for obj in objects:
                await self._session.refresh(obj)

            await self._session.commit()
        except IntegrityError as err:
            await self.__handle_integrity_error(err)

    async def _delete(self, obj: T) -> None:
        """Удаляет конкретный объект из БД."""
        await self._session.delete(obj)

        try:
            await self._session.commit()
        except IntegrityError as err:
            await self.__handle_integrity_error(err)

    async def _flush(self) -> None:
        """Flush с обработкой IntegrityError."""
        try:
            await self._session.flush()
        except IntegrityError as err:
            await self.__handle_integrity_error(err)

    async def _commit(self) -> None:
        """Коммит с обработкой IntegrityError."""
        try:
            await self._session.commit()
        except IntegrityError as err:
            await self.__handle_integrity_error(err)

    async def _rollback(self) -> None:
        """Откат транзакции."""
        await self._session.rollback()

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

    async def __handle_integrity_error(self, err: IntegrityError) -> None:
        """Откатывает транзакцию и бросает DatabaseError."""
        await self._rollback()
        raise DatabaseError(
            detail="Database query execution failed",
            ru_detail="Ошибка при выполнении запроса к базе данных",
            original_error=err,
        )
