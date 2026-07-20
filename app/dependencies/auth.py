from typing import Any

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.exceptions import AuthException, PermissionException
from app.core.response import ErrorCode
from app.core.security import decode_access_token
from app.db.session import get_db
from app.dependencies.config import get_app_settings
from app.models.user import User

bearer_scheme = HTTPBearer(
    auto_error=False,
    scheme_name="BearerAuth",
    description="输入 JWT Token（不需要 Bearer 前缀）",
)


def get_token_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    settings: Settings = Depends(get_app_settings),
) -> dict[str, Any]:
    """校验 Token；失败时不会创建数据库 Session。"""
    if credentials is None:
        raise AuthException(message="未提供认证 Token", code=ErrorCode.AUTH_REQUIRED)

    payload = decode_access_token(credentials.credentials, settings)
    if payload is None or not payload.get("sub"):
        raise AuthException(message="Token 无效或已过期", code=ErrorCode.TOKEN_INVALID)
    return payload


async def get_current_user(
    payload: dict[str, Any] = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    """根据已校验的 Token 获取当前登录用户。"""
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError):
        raise AuthException(message="Token 无效", code=ErrorCode.TOKEN_INVALID)

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise AuthException(message="Token 对应的用户不存在", code=ErrorCode.TOKEN_INVALID)
    if user.status == 0:
        raise PermissionException(message="账号已被禁用", code=ErrorCode.ACCOUNT_DISABLED)
    return user
