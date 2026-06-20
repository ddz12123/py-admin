from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import success
from app.db.session import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.response_schema import ResponseModel
from app.schemas.user_schema import UserListRequest, UserResponse
from app.schemas.user_schema import UserListResponse
from app.services import user_service

router = APIRouter(prefix="/users", tags=["用户"])


@router.get(
    "/me",
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息",
    response_model=ResponseModel[UserResponse],
)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return success(data=UserResponse.model_validate(current_user))


@router.get(
    "",
    summary="获取用户列表",
    description="分页查询用户列表，支持用户名模糊查询",
    response_model=ResponseModel[UserListResponse],
)
async def get_user_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(10, ge=1, le=100, description="每页数量"),
    username: str | None = Query(None, max_length=50, description="用户名模糊查询"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """获取用户列表

    - **page**: 页码（必填）
    - **page_size**: 每页数量（必填，最大100）
    - **username**: 用户名模糊查询（可选）
    """
    req = UserListRequest(page=page, page_size=page_size, username=username)
    result = await user_service.get_user_list(db, req)
    return success(data=result)
