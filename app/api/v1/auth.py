# -*- coding: utf-8 -*-
"""
@File    : auth.py.py
@Author  : Martin
@Time    : 2025/11/1 23:51
@Desc    : 
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.core.logging import log
from app.schemas.auth import Token, LoginRequest
from app.schemas.user import UserCreate, UserResponse
from app.crud.user import user_crud

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="注册新用户"
)
async def register(
        user_in: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    """
    注册新用户

    - **username**: 用户名（唯一）
    - **email**: 邮箱（唯一）
    - **password**: 密码
    - **full_name**: 全名（可选）
    """
    # 检查用户名是否已存在
    existing_user = await user_crud.get_by_username(db, user_in.username)
    if existing_user:
        log.warning(f"Username already exists: {user_in.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # 检查邮箱是否已存在
    existing_email = await user_crud.get_by_email(db, user_in.email)
    if existing_email:
        log.warning(f"Email already exists: {user_in.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 创建用户
    user = await user_crud.create(db, user_in)
    await db.commit()

    log.info(f"User registered: {user.id} - {user.username}")
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="用户登录"
)
async def login(
        login_data: LoginRequest,
        db: AsyncSession = Depends(get_db)
):
    """
    用户登录，返回访问令牌

    - **username**: 用户名
    - **password**: 密码
    """
    # 验证用户
    user = await user_crud.authenticate(
        db,
        username=login_data.username,
        password=login_data.password
    )

    if not user:
        log.warning(f"Failed login attempt: {login_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        log.warning(f"Inactive user login attempt: {user.id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )

    log.info(f"User logged in: {user.id} - {user.username}")

    return Token(access_token=access_token, token_type="bearer")