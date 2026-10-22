from sqlalchemy.ext.asyncio import AsyncSession

from src.payments.infrastructure.db.repository import PaymentsRepository
from src.shared.db.base.unit_of_work import SqlAlchemyUnitOfWork


class PaymentsUnitOfWork(SqlAlchemyUnitOfWork):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session)
        self.payments_repository = PaymentsRepository(session)
