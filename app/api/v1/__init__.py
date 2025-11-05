# -*- coding: utf-8 -*-
"""
@File    : __init__.py
@Author  : Martin
@Time    : 2025/11/1 22:54
@Desc    :
"""

from fastapi import APIRouter
from app.api.v1.users import router as users_router
from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.auth import router as auth_router
from app.api.v1.chat import router as chat_router

api_router = APIRouter()

# 认证路由（不需要认证）
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])

# 用户路由
api_router.include_router(users_router, prefix="/users", tags=["users"])

# API密钥路由
api_router.include_router(api_keys_router, prefix="/api-keys", tags=["api-keys"])

# 聊天路由
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
