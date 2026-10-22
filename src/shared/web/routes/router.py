from fastapi import APIRouter
from starlette import status

from src.payments.infrastructure.api.router import router as payments_router
from src.shared.web.api_settings import get_api_settings
from src.shared.web.routes.health_check import router as health_check_router
from src.shared.web.web_models import BaseWebOutputModel

api_settings = get_api_settings()
router = APIRouter(
    responses={status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": BaseWebOutputModel}},
)

v1_router = APIRouter(prefix=api_settings.api_v1_prefix)

v1_router.include_router(payments_router, tags=["payments"])

router.include_router(health_check_router)
router.include_router(v1_router)
