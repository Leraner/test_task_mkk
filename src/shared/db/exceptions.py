from src.shared.exceptions import InfrastructureError


class DatabaseError(InfrastructureError):
    """Ошибка при работе с базой данных."""

    detail = "Database operation failed"
    ru_detail = "Ошибка при работе с базой данных"
