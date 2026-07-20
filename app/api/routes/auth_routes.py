from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.response import success
from app.db.session import get_db, get_transactional_db
from app.dependencies.config import get_app_settings
from app.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.response_schema import ResponseModel
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post(
    "/register",
    summary="用户注册",
    description="注册新用户，成功后请登录获取 Token",
    response_model=ResponseModel[None],
)
async def register(
    req: RegisterRequest,
    db: AsyncSession = Depends(get_transactional_db, scope="function"),
):
    """用户注册接口。"""
    await auth_service.register(db, req)
    return success(data=None, message="注册成功")


@router.post(
    "/login",
    summary="用户登录",
    description="用户名密码登录，成功后返回 JWT Token",
    response_model=ResponseModel[TokenResponse],
)
async def login(
    req: LoginRequest,
    db: AsyncSession = Depends(get_db),
    settings: Settings = Depends(get_app_settings),
):
    """用户登录接口。"""
    result = await auth_service.login(db, req, settings)
    return success(data=result, message="登录成功")
