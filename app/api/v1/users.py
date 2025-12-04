"""
@File    : users.py.py
@Author  : Martin
@Time    : 2025/11/1 22:54
@Desc    :
"""

from app.api.deps import get_current_active_user, get_current_superuser, get_current_approved_user
from app.core.database import get_db
from app.crud.user import user_crud
import logging
from app.models.user import User
from app.schemas.user import UserListResponse, UserResponse, UserUpdate, UserPasswordUpdate
from app.schemas.response import ResponseModel
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.security import verify_password, get_password_hash

log = logging.getLogger("app")

router = APIRouter()


@router.get('/', response_model=ResponseModel[UserListResponse], summary='获取用户列表')
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
    return ResponseModel.success(data=UserListResponse(total=total, items=users))


@router.get('/me', response_model=ResponseModel[UserResponse], summary='获取当前用户信息')
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """获取当前登录用户的信息"""
    return ResponseModel.success(data=current_user)


@router.get('/{user_id}', response_model=ResponseModel[UserResponse], summary='获取指定用户信息')
async def get_user(
    user_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_approved_user)
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

    return ResponseModel.success(data=user)


@router.patch('/{user_id}', response_model=ResponseModel[UserResponse], summary='更新用户信息')
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_approved_user),
):
    """
    更新用户信息
    """
    # 检查权限
    if user_id != current_user.id and not current_user.is_superuser:
        log.warning(f'Unauthorized user update: {current_user.id} -> {user_id}')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not enough privileges')

    # 普通用户不能修改敏感字段
    if not current_user.is_superuser:
        if user_in.is_active is not None or user_in.must_change_password is not None:
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not enough privileges to update these fields')

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
    return ResponseModel.success(data=user)


@router.post('/change-password', response_model=ResponseModel[dict], summary='修改密码')
async def change_password(
    password_in: UserPasswordUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    修改当前登录用户的密码
    """
    # 验证旧密码
    if not verify_password(password_in.old_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Incorrect old password')
    
    # 更新密码
    current_user.hashed_password = get_password_hash(password_in.new_password)
    current_user.must_change_password = False
    
    db.add(current_user)
    await db.commit()
    
    log.info(f'User password changed: {current_user.id}')
    return ResponseModel.success(data={"message": "Password updated successfully"})


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
