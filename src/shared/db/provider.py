from typing import AsyncIterator

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.shared.db.db_settings import DBSettings, get_db_settings


class DbProvider(Provider):
    scope = Scope.APP

    @provide
    def get_db_settings(self) -> DBSettings:
        return get_db_settings()

    @provide
    def get_engine(self, settings: DBSettings) -> AsyncEngine:
        return create_async_engine(
            settings.connection_url,
            pool_pre_ping=settings.pool_pre_ping,
            pool_recycle=settings.pool_recycle,
        )

    @provide
    def get_session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session
