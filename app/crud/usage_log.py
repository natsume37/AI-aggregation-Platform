# -*- coding: utf-8 -*-
"""
@File    : usage_log.py.py
@Author  : Martin
@Time    : 2025/11/4 11:19
@Desc    : 
"""
from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud.base import CRUDBase
from app.models.usage_log import UsageLog
from pydantic import BaseModel


class UsageLogCreate(BaseModel):
    """创建使用记录Schema"""
    user_id: int
    conversation_id: Optional[int]
    model_name: str
    provider: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost: float
    response_time: float
    extra_data: Optional[dict] = None  # 修改这里


class UsageLogCRUD(CRUDBase[UsageLog, UsageLogCreate, BaseModel]):
    """使用记录CRUD操作"""

    async def get_user_usage(
            self,
            db: AsyncSession,
            user_id: int,
            days: int = 30
    ) -> List[UsageLog]:
        """获取用户使用记录"""
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(UsageLog)
            .where(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= start_date
            )
            .order_by(UsageLog.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_user_stats(
            self,
            db: AsyncSession,
            user_id: int,
            days: int = 30
    ) -> dict:
        """获取用户统计信息"""
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                func.sum(UsageLog.total_tokens).label("total_tokens"),
                func.sum(UsageLog.cost).label("total_cost"),
                func.count(UsageLog.id).label("request_count"),
                func.avg(UsageLog.response_time).label("avg_response_time")
            )
            .where(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= start_date
            )
        )

        row = result.one()

        return {
            "total_tokens": int(row.total_tokens or 0),
            "total_cost": float(row.total_cost or 0),
            "request_count": int(row.request_count or 0),
            "avg_response_time": float(row.avg_response_time or 0)
        }

    async def get_model_stats(
            self,
            db: AsyncSession,
            user_id: int,
            days: int = 30
    ) -> List[dict]:
        """按模型统计使用情况"""
        start_date = datetime.utcnow() - timedelta(days=days)

        result = await db.execute(
            select(
                UsageLog.model_name,
                UsageLog.provider,
                func.count(UsageLog.id).label("count"),
                func.sum(UsageLog.total_tokens).label("tokens"),
                func.sum(UsageLog.cost).label("cost")
            )
            .where(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= start_date
            )
            .group_by(UsageLog.model_name, UsageLog.provider)
        )

        return [
            {
                "model": row.model_name,
                "provider": row.provider,
                "count": row.count,
                "tokens": int(row.tokens or 0),
                "cost": float(row.cost or 0)
            }
            for row in result
        ]


# 全局实例
usage_log_crud = UsageLogCRUD(UsageLog)