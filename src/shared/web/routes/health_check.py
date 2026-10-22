from fastapi import APIRouter

from src.shared.web.web_models import BaseWebModel

router = APIRouter()


class HealthCheckOutputModel(BaseWebModel):
    status: str


@router.get("/health_check")
async def health_check() -> HealthCheckOutputModel:
    return HealthCheckOutputModel(status="ok")
