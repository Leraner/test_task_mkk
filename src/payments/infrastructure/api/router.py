from fastapi import APIRouter

from src.payments.infrastructure.api.create_payment.route import (
    router as create_payment_route,
)
from src.payments.infrastructure.api.get_payment.route import router as get_payment_route

router = APIRouter()

# Префикс - в include_router: create-роут объявлен с пустым путём, чтобы был
# POST /api/v1/payments без слеша, а FastAPI запрещает пустые и prefix, и path роутера.
router.include_router(create_payment_route, prefix="/payments")
router.include_router(get_payment_route, prefix="/payments")
