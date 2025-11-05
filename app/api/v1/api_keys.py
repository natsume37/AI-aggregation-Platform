# -*- coding: utf-8 -*-
"""
@File    : api_keys.py.py
@Author  : Martin
@Time    : 2025/11/1 22:54
@Desc    :
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.logging import log
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyListItem,
    APIKeyListResponse,
)
from app.crud.api_key import api_key_crud
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter()


@router.post(
    "/",
    response_model=APIKeyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="创建API密钥",
)
async def create_api_key(
    api_key_in: APIKeyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    为当前用户创建API密钥

    - **name**: 密钥名称
    - **description**: 描述（可选）
    - **expires_at**: 过期时间（可选）

    注意：密钥的完整值只在创建时返回一次，请妥善保管
    """
    api_key = await api_key_crud.create_for_user(db, current_user.id, api_key_in)
    await db.commit()

    log.info(f"API key created: {api_key.id} for user: {current_user.id}")
    return api_key


@router.get("/", response_model=APIKeyListResponse, summary="获取API密钥列表")
async def list_api_keys(
    skip: int = Query(0, ge=0, description="跳过的记录数"),
    limit: int = Query(100, ge=1, le=100, description="返回的记录数"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取当前用户的API密钥列表

    - 密钥只显示前8位预览
    - **skip**: 跳过的记录数
    - **limit**: 返回的记录数（最大100）
    """
    api_keys = await api_key_crud.get_by_user(
        db, user_id=current_user.id, skip=skip, limit=limit
    )

    # 转换为列表项，隐藏完整密钥
    items = [
        APIKeyListItem(
            id=key.id,
            name=key.name,
            key_preview=key.key[:8] + "..." if len(key.key) > 8 else key.key,
            is_active=key.is_active,
            expires_at=key.expires_at,
            last_used_at=key.last_used_at,
            created_at=key.created_at,
        )
        for key in api_keys
    ]

    return APIKeyListResponse(total=len(items), items=items)


@router.get("/{api_key_id}", response_model=APIKeyListItem, summary="获取API密钥详情")
async def get_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    获取指定API密钥详情

    - 只能查看自己的API密钥
    - 不返回完整密钥值
    """
    api_key = await api_key_crud.get(db, api_key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    # 检查权限
    if api_key.user_id != current_user.id:
        log.warning(f"Unauthorized API key access: {current_user.id} -> {api_key_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )

    return APIKeyListItem(
        id=api_key.id,
        name=api_key.name,
        key_preview=api_key.key[:8] + "..." if len(api_key.key) > 8 else api_key.key,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
    )


@router.patch("/{api_key_id}", response_model=APIKeyListItem, summary="更新API密钥")
async def update_api_key(
    api_key_id: int,
    api_key_in: APIKeyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    更新API密钥信息

    - 只能更新自己的API密钥
    - 可以更新名称、描述、是否启用、过期时间
    """
    api_key = await api_key_crud.get(db, api_key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    # 检查权限
    if api_key.user_id != current_user.id:
        log.warning(f"Unauthorized API key update: {current_user.id} -> {api_key_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )

    api_key = await api_key_crud.update(db, api_key, api_key_in)
    await db.commit()

    log.info(f"API key updated: {api_key.id}")

    return APIKeyListItem(
        id=api_key.id,
        name=api_key.name,
        key_preview=api_key.key[:8] + "..." if len(api_key.key) > 8 else api_key.key,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
    )


@router.delete(
    "/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT, summary="删除API密钥"
)
async def delete_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    删除API密钥

    - 只能删除自己的API密钥
    """
    api_key = await api_key_crud.get(db, api_key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    # 检查权限
    if api_key.user_id != current_user.id:
        log.warning(f"Unauthorized API key deletion: {current_user.id} -> {api_key_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )

    await api_key_crud.delete(db, api_key_id)
    await db.commit()

    log.info(f"API key deleted: {api_key_id}")
    return None


@router.post(
    "/{api_key_id}/deactivate", response_model=APIKeyListItem, summary="停用API密钥"
)
async def deactivate_api_key(
    api_key_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    停用API密钥

    - 停用后的密钥将无法使用
    - 可以通过更新接口重新启用
    """
    api_key = await api_key_crud.get(db, api_key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="API key not found"
        )

    # 检查权限
    if api_key.user_id != current_user.id:
        log.warning(
            f"Unauthorized API key deactivation: {current_user.id} -> {api_key_id}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough privileges"
        )

    api_key = await api_key_crud.deactivate(db, api_key)
    await db.commit()

    log.info(f"API key deactivated: {api_key.id}")

    return APIKeyListItem(
        id=api_key.id,
        name=api_key.name,
        key_preview=api_key.key[:8] + "..." if len(api_key.key) > 8 else api_key.key,
        is_active=api_key.is_active,
        expires_at=api_key.expires_at,
        last_used_at=api_key.last_used_at,
        created_at=api_key.created_at,
    )
