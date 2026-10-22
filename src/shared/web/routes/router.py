from fastapi import APIRouter
from starlette import status

from shared.web.api_settings import get_api_settings
from shared.web.routes.health_check import router as health_check_router

api_settings = get_api_settings()
router = APIRouter(
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": BaseWebOutputModel}},
)

v1_router = APIRouter(prefix=api_settings.api_v1_prefix)


router.include_router(health_check_router)
router.include_router(v1_router)
