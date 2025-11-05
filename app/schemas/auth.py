"""
@File    : auth.py.py
@Author  : Martin
@Time    : 2025/11/1 23:50
@Desc    :
"""

from pydantic import BaseModel

class Token(BaseModel):
    """令牌响应"""

    access_token: str
    token_type: str = 'bearer'


class TokenData(BaseModel):
    """令牌数据"""

    user_id: int | None = None
    username: str | None = None


class LoginRequest(BaseModel):
    """登录请求"""

    username: str
    password: str
