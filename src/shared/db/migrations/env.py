import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

# Импорт моделей регистрирует их таблицы в BaseDBModel.metadata — без него autogenerate
# не увидит таблиц. Новый bounded context — добавить сюда импорт его моделей.
from src.payments.infrastructure.db.models import OutboxEventDBModel, PaymentDBModel  # noqa: F401
from src.shared.db.base.models import BaseDBModel
from src.shared.db.db_settings import get_db_settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = BaseDBModel.metadata

# URL берётся из тех же настроек, что и у приложения (POSTGRES_* из env), а не из alembic.ini.
DATABASE_URL = get_db_settings().connection_url


def _configure(**kwargs) -> None:
    context.configure(
        target_metadata=target_metadata,
        compare_server_default=True,
        **kwargs,
    )


def run_migrations_offline() -> None:
    """Генерирует SQL без подключения к БД (`alembic upgrade head --sql`)."""
    _configure(
        url=DATABASE_URL,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    _configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Применяет миграции через async-движок (asyncpg); NullPool — соединение одноразовое."""
    engine = create_async_engine(DATABASE_URL, poolclass=pool.NullPool)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
