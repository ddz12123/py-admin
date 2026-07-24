from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ServiceUnavailableException
from app.core.openapi import error_responses
from app.core.response import ErrorCode, success
from app.db.session import get_db
from app.schemas.response_schema import ResponseModel
from app.schemas.system_schema import HealthResponse, ReadinessResponse

router = APIRouter(prefix="/system", tags=["系统"])


@router.get("/health", response_model=ResponseModel[HealthResponse])
@router.get("/health/live", response_model=ResponseModel[HealthResponse])
async def health_check():
    """应用存活检查，不访问外部依赖。"""
    return success(data=HealthResponse(status="ok"))


@router.get(
    "/health/ready",
    response_model=ResponseModel[ReadinessResponse],
    responses=error_responses(503),
)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """应用就绪检查，验证数据库连接。"""
    try:
        await db.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise ServiceUnavailableException(
            message="数据库暂不可用",
            code=ErrorCode.DATABASE_UNAVAILABLE,
            data={"database": "error"},
        ) from exc
    return success(data=ReadinessResponse(status="ok", database="ok"))
