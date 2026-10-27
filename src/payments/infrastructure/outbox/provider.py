from dishka import Provider, Scope, from_context, provide
from faststream.rabbit import RabbitBroker

from src.payments.domain.interfaces.unit_of_work import IPaymentsUnitOfWork
from src.payments.infrastructure.db.unit_of_work import PaymentsUnitOfWork
from src.payments.infrastructure.outbox.relay import OutboxRelay


class OutboxRelayProvider(Provider):
    scope = Scope.REQUEST

    broker = from_context(provides=RabbitBroker, scope=Scope.APP)
    unit_of_work = provide(PaymentsUnitOfWork, provides=IPaymentsUnitOfWork)
    relay = provide(OutboxRelay)
