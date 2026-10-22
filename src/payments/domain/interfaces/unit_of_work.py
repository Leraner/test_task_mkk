from typing import Protocol

from src.payments.domain.interfaces.repository import IPaymentsRepository
from src.shared_kernel.interfaces.unit_of_work import IUnitOfWork


class IPaymentsUnitOfWork(IUnitOfWork, Protocol):
    payments: IPaymentsRepository
