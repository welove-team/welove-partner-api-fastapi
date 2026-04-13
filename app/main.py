import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse

from app.routes.health_check import router as health_check_router
from app.routes.verify_member import router as verify_member_router

app = FastAPI(
    title="welove 파트너 교회 API",
    description="welove 파트너 교회 API 보일러플레이트 (FastAPI + Python)",
    version=os.environ.get("APP_VERSION", "1.0.0"),
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """에러 응답 형식을 스펙에 맞게 통일합니다: { error, message }"""
    detail = exc.detail
    if isinstance(detail, dict):
        return JSONResponse(status_code=exc.status_code, content=detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "ERROR", "message": str(detail)},
    )

app.include_router(health_check_router)
app.include_router(verify_member_router)
