from dishka import Provider, Scope, provide, provide_all

from src.payments.application.use_cases.create_payment import CreatePaymentUseCase
from src.payments.application.use_cases.get_payment import GetPaymentUseCase
from src.payments.domain.interfaces.repository import IPaymentsRepository
from src.payments.domain.interfaces.unit_of_work import IPaymentsUnitOfWork
from src.payments.infrastructure.api.create_payment.presenter import CreatePaymentPresenter
from src.payments.infrastructure.api.get_payment.presenter import GetPaymentPresenter
from src.payments.infrastructure.db.repository import PaymentsRepository
from src.payments.infrastructure.db.unit_of_work import PaymentsUnitOfWork


class PaymentsProvider(Provider):
    scope = Scope.REQUEST

    repository = provide(PaymentsRepository, provides=IPaymentsRepository)
    unit_of_work = provide(PaymentsUnitOfWork, provides=IPaymentsUnitOfWork)

    use_cases = provide_all(
        CreatePaymentUseCase,
        GetPaymentUseCase,
    )

    presenters = provide_all(
        CreatePaymentPresenter,
        GetPaymentPresenter,
        scope=Scope.APP,
    )
