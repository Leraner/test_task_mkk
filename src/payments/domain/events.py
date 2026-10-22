from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PaymentCreated:
    payment_id: UUID
