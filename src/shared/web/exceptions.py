from src.shared.exceptions import InfrastructureError


class InvalidApiKeyError(InfrastructureError):
    detail = "Invalid or missing API key"
    ru_detail = "Неверный или отсутствующий API-ключ"
