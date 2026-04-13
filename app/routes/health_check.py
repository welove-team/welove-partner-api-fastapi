import os
from datetime import datetime, timezone

from fastapi import APIRouter

from app.models import HealthCheckResponse

router = APIRouter()


@router.get("/health-check", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """
    GET /health-check

    welove가 서버 가용성을 확인하기 위해 주기적으로 호출합니다.
    인증 없이 호출됩니다.
    """
    return HealthCheckResponse(
        status="ok",
        version=os.environ.get("APP_VERSION", "1.0.0"),
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
