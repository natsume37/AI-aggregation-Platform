"""
@File    : users.py.py
@Author  : Martin
@Time    : 2025/11/1 22:54
@Desc    :
"""

from app.api.deps import get_current_active_user, get_current_superuser
from app.core.database import get_db
from app.crud.user import user_crud
from app.main import log
from app.models.user import User
from app.schemas.user import UserListResponse, UserResponse, UserUpdate
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.get('/', response_model=UserListResponse, summary='获取用户列表')
async def list_users(
    skip: int = Query(0, ge=0, description='跳过的记录数'),
    limit: int = Query(100, ge=1, le=100, description='返回的记录数'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    """
    获取用户列表（仅超级管理员）
    """
    users = await user_crud.get_multi(db, skip=skip, limit=limit)
    total = await user_crud.get_count(db)

    log.info(f'User list retrieved by superuser: {current_user.id}')
    return UserListResponse(total=total, items=users)


@router.get('/me', response_model=UserResponse, summary='获取当前用户信息')
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户的信息"""
    return current_user


@router.get('/{user_id}', response_model=UserResponse, summary='获取指定用户信息')
async def get_user(
    user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """
    获取指定用户信息

    - 普通用户只能查看自己的信息
    - 超级管理员可以查看所有用户信息
    """
    # 检查权限
    if user_id != current_user.id and not current_user.is_superuser:
        log.warning(f'Unauthorized user info access: {current_user.id} -> {user_id}')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not enough privileges')

    user = await user_crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    return user


@router.patch('/{user_id}', response_model=UserResponse, summary='更新用户信息')
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新用户信息
    """
    # 检查权限
    if user_id != current_user.id and not current_user.is_superuser:
        log.warning(f'Unauthorized user update: {current_user.id} -> {user_id}')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not enough privileges')

    user = await user_crud.get(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    # 检查邮箱是否已被使用
    if user_in.email:
        existing_email = await user_crud.get_by_email(db, user_in.email)
        if existing_email and existing_email.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Email already registered')

    user = await user_crud.update(db, user, user_in)
    await db.commit()

    log.info(f'User updated: {user.id}')
    return user


@router.delete('/{user_id}', status_code=status.HTTP_204_NO_CONTENT, summary='删除用户')
async def delete_user(
    user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_superuser)
):
    """
    删除用户（仅超级管理员）
    """
    success = await user_crud.delete(db, user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='User not found')

    await db.commit()
    log.info(f'User deleted: {user_id} by superuser: {current_user.id}')
    return None
