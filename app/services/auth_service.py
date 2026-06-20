from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse


async def register(db: AsyncSession, req: RegisterRequest) -> None:
    """用户注册"""
    user = User(
        username=req.username,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise AppException(message="用户名已存在")


async def login(db: AsyncSession, req: LoginRequest) -> TokenResponse:
    """用户登录"""
    stmt = select(User).where(User.username == req.username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise AppException(message="用户名或密码错误")

    if user.status == 0:
        raise AppException(message="账号已被禁用")

    token = create_access_token(data={"sub": str(user.id), "username": user.username})
    return TokenResponse(access_token=token)
