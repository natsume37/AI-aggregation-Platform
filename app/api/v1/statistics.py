from app.api.deps import get_current_superuser
from app.core.database import get_db
from app.crud.usage_log import usage_log_crud
from app.models.user import User
from app.schemas.response import ResponseModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get('/summary', response_model=ResponseModel[dict], summary='获取全局统计摘要')
async def get_global_summary(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    获取全局统计摘要（仅超级管理员）
    包含：总Token数、总成本、总请求数、平均响应时间
    """
    data = await usage_log_crud.get_global_stats(db, days=days)
    return ResponseModel.success(data=data)


@router.get('/models', response_model=ResponseModel[list[dict]], summary='获取全局模型使用统计')
async def get_global_model_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    获取全局模型使用统计（仅超级管理员）
    """
    data = await usage_log_crud.get_global_model_stats(db, days=days)
    return ResponseModel.success(data=data)


@router.get('/daily', response_model=ResponseModel[list[dict]], summary='获取每日使用趋势')
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    获取每日使用趋势（仅超级管理员）
    """
    data = await usage_log_crud.get_daily_stats(db, days=days)
    return ResponseModel.success(data=data)
