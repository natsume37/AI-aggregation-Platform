"""
@File    : api_key.py.py
@Author  : Martin
@Time    : 2025/11/1 22:51
@Desc    :
"""

import secrets
from app.crud.base import CRUDBase
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyUpdate
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDAPIKey(CRUDBase[APIKey, APIKeyCreate, APIKeyUpdate]):
    """API密钥CRUD操作"""

    def generate_key(self, prefix: str = 'sk') -> str:
        """生成API密钥"""
        random_part = secrets.token_urlsafe(32)
        return f'{prefix}_{random_part}'

    async def get_by_key(self, db: AsyncSession, key: str) -> APIKey | None:
        """根据密钥获取记录"""
        result = await db.execute(select(APIKey).where(APIKey.key == key))
        return result.scalar_one_or_none()

    async def get_by_user(self, db: AsyncSession, user_id: int, skip: int = 0, limit: int = 100) -> list[APIKey]:
        """获取用户的所有密钥"""
        result = await db.execute(select(APIKey).where(APIKey.user_id == user_id).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def get_active_by_key(self, db: AsyncSession, key: str) -> APIKey | None:
        """获取有效的API密钥（检查是否激活和过期）"""
        result = await db.execute(select(APIKey).where(APIKey.key == key, APIKey.is_active == True))
        api_key = result.scalar_one_or_none()

        if api_key and api_key.expires_at:
            if api_key.expires_at < datetime.now(api_key.expires_at.tzinfo):
                return None

        return api_key

    async def create_for_user(self, db: AsyncSession, user_id: int, obj_in: APIKeyCreate) -> APIKey:
        """为用户创建API密钥"""
        api_key = self.generate_key()

        db_obj = APIKey(
            key=api_key, name=obj_in.name, user_id=user_id, description=obj_in.description, expires_at=obj_in.expires_at
        )

        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update_last_used(self, db: AsyncSession, api_key: APIKey) -> APIKey:
        """更新最后使用时间"""
        api_key.last_used_at = datetime.now(api_key.created_at.tzinfo)
        db.add(api_key)
        await db.flush()
        await db.refresh(api_key)
        return api_key

    async def deactivate(self, db: AsyncSession, api_key: APIKey) -> APIKey:
        """停用API密钥"""
        api_key.is_active = False
        db.add(api_key)
        await db.flush()
        await db.refresh(api_key)
        return api_key


# 创建全局实例
api_key_crud = CRUDAPIKey(APIKey)
