from src.payments.domain.entities import Payment
from src.payments.infrastructure.db.models import PaymentDBModel
from src.shared.db.base.repository import BaseRepository


class PaymentsRepository(BaseRepository[PaymentDBModel, Payment]):
    model = PaymentDBModel
