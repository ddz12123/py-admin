from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthException, ConflictException, PermissionException
from app.core.response import ErrorCode
from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth_schema import LoginRequest, RegisterRequest, TokenResponse


async def register(db: AsyncSession, req: RegisterRequest) -> None:
    """注册用户。事务由 get_transactional_db 统一管理。"""
    user = User(username=req.username, hashed_password=hash_password(req.password))
    db.add(user)
    try:
        # 提前触发唯一约束，异常由事务依赖统一回滚。
        await db.flush()
    except IntegrityError as exc:
        raise ConflictException(
            message="用户名已存在",
            code=ErrorCode.USERNAME_EXISTS,
        ) from exc


async def login(db: AsyncSession, req: LoginRequest, settings: Settings) -> TokenResponse:
    """用户登录。"""
    result = await db.execute(select(User).where(User.username == req.username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise AuthException(
            message="用户名或密码错误",
            code=ErrorCode.INVALID_CREDENTIALS,
        )
    if user.status == 0:
        raise PermissionException(
            message="账号已被禁用",
            code=ErrorCode.ACCOUNT_DISABLED,
        )

    token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        settings=settings,
    )
    return TokenResponse(access_token=token)
