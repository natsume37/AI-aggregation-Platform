"""
@File    : auth.py.py
@Author  : Martin
@Time    : 2025/11/1 23:51
@Desc    :
"""

from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token
from app.crud.user import user_crud
import logging
from app.schemas.auth import LoginRequest, Token
from app.schemas.response import ResponseModel
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

log = logging.getLogger("app")

router = APIRouter()


@router.post('/login', response_model=ResponseModel[Token], summary='管理员登录')
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    管理员登录，返回访问令牌

    - **username**: 用户名
    - **password**: 密码
    """
    # 验证用户
    user = await user_crud.authenticate(db, username=login_data.username, password=login_data.password)

    if not user:
        log.warning(f'Failed login attempt: {login_data.username}')
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    if not user.is_active:
        log.warning(f'Inactive user login attempt: {user.id}')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Inactive user')

    # 检查是否为管理员 (可选，如果只允许管理员登录)
    # if not user.is_superuser and not user.is_admin:
    #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not authorized')

    # 创建访问令牌
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': str(user.id), 'username': user.username}, expires_delta=access_token_expires
    )

    log.info(f'User logged in: {user.id} - {user.username}')

    return ResponseModel.success(data=Token(access_token=access_token, token_type='bearer'))
