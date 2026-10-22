from __future__ import annotations


class InfrastructureError(Exception):
    """Базовая ошибка инфраструктурного слоя."""

    detail = "Unknown error"
    ru_detail = "Неизвестная ошибка"
    extra: dict | None = None

    def __init__(
        self,
        detail: str | None = None,
        ru_detail: str | None = None,
        original_error: Exception | None = None,
        **kwargs,
    ):
        self.detail = detail if detail else self.detail
        self.ru_detail = ru_detail if ru_detail else self.ru_detail
        self.original_error = original_error
        self.extra = kwargs if kwargs else self.extra
        super().__init__(self.detail)
