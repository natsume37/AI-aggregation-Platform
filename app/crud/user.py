"""
@File    : user.py.py
@Author  : Martin
@Time    : 2025/11/1 22:50
@Desc    :
"""

from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户CRUD操作"""

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        """根据邮箱获取用户"""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, db: AsyncSession, username: str) -> User | None:
        """根据用户名获取用户"""
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj_in: UserCreate) -> User:
        """创建用户（重写以处理密码加密）"""
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
        )
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: User, obj_in: UserUpdate) -> User:
        """更新用户（重写以处理密码加密）"""
        update_data = obj_in.model_dump(exclude_unset=True)

        if 'password' in update_data:
            hashed_password = get_password_hash(update_data['password'])
            del update_data['password']
            update_data['hashed_password'] = hashed_password

        return await super().update(db, db_obj, update_data)

    async def authenticate(self, db: AsyncSession, username: str, password: str) -> User | None:
        """验证用户身份"""
        user = await self.get_by_username(db, username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


# 创建全局实例
user_crud = CRUDUser(User)
