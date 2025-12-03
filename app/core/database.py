"""
@File    : database.py.py
@Author  : Martin
@Time    : 2025/11/1 22:47
@Desc    :
"""

from app.core.config import settings
import logging
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

log = logging.getLogger("app")

class Base(DeclarativeBase):
    """SQLAlchemy基础模型类"""

    pass


# 创建异步引擎
engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,  # 开发环境显示SQL
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,  # 连接池预检查
    pool_recycle=3600,  # 1小时回收连接
)

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False, autocommit=False, autoflush=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    用于FastAPI依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            log.error(f'Database session error: {e}')
            raise
        finally:
            await session.close()


async def init_db():
    """初始化数据库（仅用于测试）"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info('Database initialized')


async def close_db():
    """关闭数据库连接"""
    await engine.dispose()
    log.info('Database connection closed')


def get_engine():
    """返回全局的 async engine（用于健康检查）"""
    return engine
