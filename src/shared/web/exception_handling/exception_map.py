"""
Мапа доменных и инфраструктурных исключений на HTTP статус-коды.

Используется exception-handler'ом FastAPI, чтобы по типу пойманного
исключения выбрать корректный статус ответа, не размазывая эту логику
по роутерам bounded contexts.

Starlette ищет handler по MRO исключения, поэтому наследники уже
замапленных классов (например, `InvalidPaymentAmountError` от
`EntityValidationError`) отдельно добавлять не нужно.

Структура:
    CORE_DOMAIN_EXCEPTIONS_TO_STATUS_CODES — базовые доменные ошибки из
        `shared_kernel.exceptions`, общие для всех bounded contexts
        (не найдено / уже существует / ошибка валидации / нет прав).
    LOGICAL_EXCEPTIONS_TO_STATUS_CODES — специфичные для конкретных
        bounded contexts доменные ошибки (наследники `DomainError`, не
        сводимые к базовой CRUD-семантике сущности).
    DOMAIN_EXCEPTIONS_TO_STATUS_CODES — объединение двух мап выше; именно
        она используется handler'ом.
    INFRASTRUCTURE_EXCEPTIONS_TO_STATUS_CODES — ошибки инфраструктурного
        слоя (БД), см. `shared.exceptions.InfrastructureError`.
"""

from starlette import status

from src.payments.domain.exceptions import PaymentAlreadyProcessedError
from src.shared.db.exceptions import DatabaseError
from src.shared_kernel.exceptions import (
    EntityAlreadyExistError,
    EntityNotFoundError,
    EntityValidationError,
    PermissionDeniedError,
)

CORE_DOMAIN_EXCEPTIONS_TO_STATUS_CODES = {
    EntityNotFoundError: status.HTTP_404_NOT_FOUND,
    EntityAlreadyExistError: status.HTTP_409_CONFLICT,
    EntityValidationError: status.HTTP_422_UNPROCESSABLE_CONTENT,
    PermissionDeniedError: status.HTTP_403_FORBIDDEN,
}

LOGICAL_EXCEPTIONS_TO_STATUS_CODES = {
    PaymentAlreadyProcessedError: status.HTTP_409_CONFLICT,
}

DOMAIN_EXCEPTIONS_TO_STATUS_CODES = {
    **CORE_DOMAIN_EXCEPTIONS_TO_STATUS_CODES,
    **LOGICAL_EXCEPTIONS_TO_STATUS_CODES,
}

INFRASTRUCTURE_EXCEPTIONS_TO_STATUS_CODES = {
    DatabaseError: status.HTTP_503_SERVICE_UNAVAILABLE,
}
