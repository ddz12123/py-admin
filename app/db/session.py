from collections.abc import AsyncGenerator
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import DatabaseSettings

SessionFactory = async_sessionmaker[AsyncSession]


def create_db_engine(settings: DatabaseSettings) -> AsyncEngine:
    """根据数据库领域配置创建异步引擎。"""
    engine_options: dict[str, Any] = {
        "echo": settings.SQL_ECHO,
        "pool_pre_ping": True,
    }
    if settings.DATABASE_URL.startswith("mysql"):
        engine_options.update(
            {
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_recycle": settings.DB_POOL_RECYCLE,
            }
        )
    return create_async_engine(settings.DATABASE_URL, **engine_options)


def create_session_factory(engine: AsyncEngine) -> SessionFactory:
    """创建异步 Session 工厂。"""
    return async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


def get_session_factory(request: Request) -> SessionFactory:
    """从应用实例获取 Session 工厂。"""
    return request.app.state.db_session_factory


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """只管理 Session 生命周期，不自动提交事务，适用于查询场景。"""
    session_factory = get_session_factory(request)
    async with session_factory() as session:
        yield session


async def get_transactional_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """提供请求级事务：正常结束自动提交，出现异常自动回滚。"""
    session_factory = get_session_factory(request)
    async with session_factory.begin() as session:
        yield session
