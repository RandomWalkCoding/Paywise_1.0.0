from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    timestamp: datetime

router = APIRouter(tags=["system"])


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="paywise-api",
        version=settings.app_version,
        timestamp=datetime.now(timezone.utc),
    )
