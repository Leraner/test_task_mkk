from src.shared_kernel.exceptions import DomainError, EntityValidationError


class PaymentError(DomainError):
    detail = "Payment error"
    ru_detail = "Ошибка платежа"


class PaymentAlreadyProcessedError(PaymentError):
    detail = "Payment is already processed"
    ru_detail = "Платёж уже обработан"


class InvalidPaymentAmountError(EntityValidationError, PaymentError):
    detail = "Payment amount must be positive and have at most 2 decimal places"
    ru_detail = (
        "Сумма платежа должна быть положительной и содержать не более 2 знаков после запятой"
    )


class InvalidIdempotencyKeyError(EntityValidationError, PaymentError):
    detail = "Idempotency key must not be empty"
    ru_detail = "Ключ идемпотентности не должен быть пустым"


class InvalidWebhookUrlError(EntityValidationError, PaymentError):
    detail = "Webhook URL must be an absolute http(s) URL"
    ru_detail = "Webhook URL должен быть абсолютным http(s) адресом"
