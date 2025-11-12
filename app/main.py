"""
@File    : main.py
@Author  : Martin
@Time    : 2025/11/1 22:38
@Desc    : FastAPI 应用启动入口
"""

import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import uvicorn

# import the log and load it
from app.core.logger import setup_logging

log = setup_logging()

from app.api.v1 import api_router
from app.core.config import settings
from app.core.database import close_db, get_engine


# ==================== 数据库健康检查 ====================
async def check_db_connection() -> bool:
    """尝试连接数据库，成功返回 True"""
    try:
        engine = get_engine()  # 你的 get_engine() 返回 async_engine
        async with engine.begin() as conn:
            await conn.execute(text('SELECT 1;'))
        log.info('✅ 数据库连接成功')
        return True
    except Exception as e:
        log.error(f'❌ 数据库连接失败: {e}')
        return False


# ==================== 生命周期管理 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    log.info(f"🚀 启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    log.info(f"🌍 环境: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")

    if not await check_db_connection():
        log.critical('❌ 启动失败：无法连接数据库')
        sys.exit(1)  # 直接退出进程

    yield  # === 应用运行期间 ===

    # 应用关闭时
    log.info('🛑 应用关闭中...')
    await close_db()


# ==================== 创建 FastAPI 应用 ====================
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description='FastAPI AI 聚合后台系统',
    docs_url='/docs' if settings.DEBUG else None,
    redoc_url='/redoc' if settings.DEBUG else None,
    openapi_url='/openapi.json' if settings.DEBUG else None,
    lifespan=lifespan,
)

# ==================== CORS 配置 ====================
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'] if settings.DEBUG else ['https://yourdomain.com'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# ==================== 注册路由 ====================
app.include_router(api_router, prefix='/api/v1')


# ==================== 基础接口 ====================
@app.get('/', tags=['root'])
async def root():
    """根路径"""
    return {
        'message': f'Welcome to {settings.APP_NAME}',
        'version': settings.APP_VERSION,
        'environment': settings.ENVIRONMENT,
        'docs': '/docs' if settings.DEBUG else 'disabled',
    }


@app.get('/health', tags=['health'])
async def health_check():
    """健康检查 + 数据库状态"""
    db_status = 'connected' if await check_db_connection() else 'failed'
    return {
        'status': 'healthy' if db_status == 'connected' else 'unhealthy',
        'version': settings.APP_VERSION,
        'environment': settings.ENVIRONMENT,
        'database': db_status,
    }


# ==================== 启动入口 ====================
if __name__ == '__main__':
    log.info("🔧 启动 uvicorn 服务...")
    uvicorn.run(
        'app.main:app',
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
