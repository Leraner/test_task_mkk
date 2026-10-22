from fastapi import APIRouter

from src.payments.infrastructure.api.create_payment.route import (
    router as create_payment_route,
)
from src.payments.infrastructure.api.get_payment.route import router as get_payment_route

router = APIRouter(prefix="/payments")


router.include_router(create_payment_route)
router.include_router(get_payment_route)
