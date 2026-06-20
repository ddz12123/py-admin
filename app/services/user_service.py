from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user_schema import UserListRequest, UserListResponse, UserResponse


async def get_user_list(db: AsyncSession, req: UserListRequest) -> UserListResponse:
    """获取用户列表"""
    # 构建查询条件
    query = select(User).order_by(User.id.desc())
    count_query = select(func.count()).select_from(User)

    # 用户名模糊查询
    if req.username:
        query = query.where(User.username.like(f"%{req.username}%"))
        count_query = count_query.where(User.username.like(f"%{req.username}%"))

    # 查询总数
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # 分页查询
    query = query.offset((req.page - 1) * req.page_size).limit(req.page_size)
    result = await db.execute(query)
    users = result.scalars().all()

    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=req.page,
        page_size=req.page_size,
    )
