"""
@File    : deps.py.py
@Author  : Martin
@Time    : 2025/11/1 22:53
@Desc    :
"""

from app.core.config import settings
from app.core.database import get_db
from app.crud.api_key import api_key_crud
from app.crud.user import user_crud
import logging
from app.models.api_key import APIKey
from app.models.user import User

log = logging.getLogger("app")
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

# HTTP Bearer 认证方案
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security), db: AsyncSession = Depends(get_db)
) -> User:
    """
    从JWT token获取当前用户
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials

    try:
        # 解码JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get('sub')
        if user_id is None:
            raise credentials_exception
    except JWTError as e:
        log.warning(f'JWT decode error: {e}')
        raise credentials_exception

    # 从数据库获取用户
    user = await user_crud.get(db, int(user_id))
    if user is None:
        log.warning(f'User not found: {user_id}')
        raise credentials_exception

    if not user.is_active:
        log.warning(f'Inactive user attempted access: {user_id}')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Inactive user')

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """获取当前激活用户"""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Inactive user')
    return current_user


async def get_current_approved_user(current_user: User = Depends(get_current_active_user)) -> User:
    """获取当前激活且不需要修改密码的用户"""
    if current_user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail='Password change required. Please update your password first.'
        )
    return current_user


async def get_current_superuser(current_user: User = Depends(get_current_approved_user)) -> User:
    """获取当前超级用户"""
    if not current_user.is_superuser:
        log.warning(f'Non-superuser attempted superuser action: {current_user.id}')
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not enough privileges')
    return current_user


async def verify_api_key(
    x_api_key: str | None = Header(None, alias='X-API-Key'),
    authorization: str | None = Header(None, alias='Authorization'),
    db: AsyncSession = Depends(get_db)
) -> APIKey:
    """
    验证API密钥
    用于API密钥认证的接口
    """
    api_key_value = x_api_key
    
    # If X-API-Key is missing, try to extract from Authorization header
    if not api_key_value and authorization:
        if authorization.startswith("Bearer "):
            api_key_value = authorization.split(" ")[1]
            
    if not api_key_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail='API key required', headers={'WWW-Authenticate': 'ApiKey'}
        )

    api_key_obj = await api_key_crud.get_active_by_key(db, api_key_value)

    if not api_key_obj:
        log.warning(f'Invalid API key attempted: {api_key_value[:8]}...')
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired API key')

    # 检查用户是否必须修改密码
    # 注意：这里需要确保 api_key_obj.user 是加载的，或者我们需要重新查询用户
    # 通常 APIKey 模型定义了 relationship('User', lazy='joined') 或者我们需要显式加载
    # 假设 APIKey 模型中 user 关系是 lazy='select' (默认)，我们需要 await api_key_obj.awaitable_attrs.user
    # 或者在 CRUD 中使用 joinedload
    
    # 为了简单起见，我们这里直接查询用户状态
    user = await user_crud.get(db, api_key_obj.user_id)
    if not user or not user.is_active:
         raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User inactive')
         
    if user.must_change_password:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail='Password change required. Please update your password via web interface first.'
        )

    # 更新最后使用时间（异步，不等待）
    await api_key_crud.update_last_used(db, api_key_obj)

    return api_key_obj


async def get_user_from_api_key(api_key: APIKey, db: AsyncSession) -> User:
    """从API Key获取用户"""
    user = await user_crud.get(db, api_key.user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='User not found')
    return user


# 可选的认证：支持 JWT 或 API Key
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_api_key: str | None = Header(None, alias='X-API-Key'),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    可选认证：尝试从JWT或API Key获取用户
    如果都没有，返回None（用于公开接口）
    """
    # 先尝试JWT
    if credentials:
        try:
            return await get_current_user(credentials, db)
        except HTTPException:
            pass

    # 再尝试API Key
    if x_api_key:
        try:
            api_key_obj = await verify_api_key(x_api_key, db)
            return await get_user_from_api_key(api_key_obj, db)
        except HTTPException:
            pass

    return None
