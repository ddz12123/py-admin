from fastapi import APIRouter

from app.core.response import success
from app.schemas.response_schema import ResponseModel
from app.schemas.system_schema import HealthResponse

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/health", response_model=ResponseModel[HealthResponse])
async def health_check():
    """健康检查"""
    return success(data=HealthResponse(status="ok"))
