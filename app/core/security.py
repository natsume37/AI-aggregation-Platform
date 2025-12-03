"""
@File    : security.py.py
@Author  : Martin
@Time    : 2025/11/1 23:50
@Desc    :
"""

from app.core.config import settings
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext

# 密码加密上下文
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """创建访问令牌"""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)
