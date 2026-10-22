from src.payments.infrastructure.provider import PaymentsProvider
from src.shared.db.provider import DbProvider


def get_providers_list() -> list:
    return [DbProvider(), PaymentsProvider()]
