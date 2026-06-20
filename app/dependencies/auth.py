from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthException
from app.db.session import get_db
from app.models.user import User


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """获取当前登录用户（从中间件解析的 request.state 获取）"""
    user_id = getattr(request.state, "user_id", None)

    if not user_id:
        raise AuthException(message="未登录")

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        raise AuthException(message="Token 无效")

    stmt = select(User).where(User.id == user_id_int)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None:
        raise AuthException(message="用户不存在")
    if user.status == 0:
        raise AuthException(message="账号已被禁用")

    return user
