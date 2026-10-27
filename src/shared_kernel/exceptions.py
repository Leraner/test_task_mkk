class DomainError(Exception):
    detail = "Unknown error"
    ru_detail = "Неизвестная ошибка"
    extra: dict | None = None

    def __init__(
        self,
        detail: str | None = None,
        ru_detail: str | None = None,
        **kwargs,
    ) -> None:
        self.detail = self.detail if not detail else detail
        self.ru_detail = self.ru_detail if not ru_detail else ru_detail
        self.extra = self.extra if not kwargs else kwargs
        super().__init__(self.detail)


class EntityNotFoundError(DomainError):
    detail = "Entity not found"
    ru_detail = "Запись не найдена"


class EntityAlreadyExistError(DomainError):
    detail = "Entity already exist"
    ru_detail = "Запись уже существует"


class EntityValidationError(DomainError):
    detail = "Entity validation error"
    ru_detail = "Ошибка валидации записи"


class PermissionDeniedError(DomainError):
    detail = "Permission denied"
    ru_detail = "Недостаточно прав"
