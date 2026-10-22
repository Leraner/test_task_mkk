from src.shared.exceptions import InfrastructureError

UNIQUE_VIOLATION_SQLSTATE = "23505"


class DatabaseError(InfrastructureError):
    """Ошибка при работе с базой данных."""

    detail = "Database operation failed"
    ru_detail = "Ошибка при работе с базой данных"

    def is_unique_violation(self, constraint_name: str) -> bool:
        """Вызвана ли ошибка нарушением уникального ограничения `constraint_name`.

        `original_error.orig` — ошибка драйвера в обёртке SQLAlchemy (с `sqlstate`),
        её `__cause__` — исходная ошибка asyncpg (с `constraint_name`).
        """
        orig = getattr(self.original_error, "orig", None)
        return (
            getattr(orig, "sqlstate", None) == UNIQUE_VIOLATION_SQLSTATE
            and getattr(orig.__cause__, "constraint_name", None) == constraint_name
        )
