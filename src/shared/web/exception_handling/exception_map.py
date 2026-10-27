from starlette import status

from src.payments.domain.exceptions import PaymentAlreadyProcessedError
from src.shared.db.exceptions import DatabaseError
from src.shared.web.exceptions import InvalidApiKeyError
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

WEB_EXCEPTIONS_TO_STATUS_CODES = {
    InvalidApiKeyError: status.HTTP_401_UNAUTHORIZED,
}
