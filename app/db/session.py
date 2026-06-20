from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

engine_options = {
    "echo": settings.DEBUG,
    "future": True,
    "pool_pre_ping": True,  # 连接前 ping 检测
}

# MySQL 生产/开发连接池配置；SQLite 等测试库不支持这些参数
if settings.DATABASE_URL.startswith("mysql"):
    engine_options.update(
        {
            "pool_size": 10,       # 连接池大小
            "max_overflow": 20,    # 最大溢出连接数
            "pool_recycle": 3600,  # 连接回收时间（秒）
        }
    )

engine = create_async_engine(settings.DATABASE_URL, **engine_options)

# 创建异步 Session 工厂
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库 Session（依赖注入用）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
