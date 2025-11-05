"""
@File    : api_key.py.py
@Author  : Martin
@Time    : 2025/11/1 22:49
@Desc    :
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# 基础Schema
class APIKeyBase(BaseModel):
    """API密钥基础Schema"""

    name: str = Field(..., min_length=1, max_length=100, description='密钥名称')
    description: str | None = Field(None, description='描述')
    expires_at: datetime | None = Field(None, description='过期时间')


# 创建API密钥Schema
class APIKeyCreate(APIKeyBase):
    """创建API密钥Schema"""

    pass


# 更新API密钥Schema
class APIKeyUpdate(BaseModel):
    """更新API密钥Schema"""

    name: str | None = Field(None, min_length=1, max_length=100, description='密钥名称')
    description: str | None = Field(None, description='描述')
    is_active: bool | None = Field(None, description='是否启用')
    expires_at: datetime | None = Field(None, description='过期时间')


# 响应Schema
class APIKeyResponse(APIKeyBase):
    """API密钥响应Schema"""

    id: int
    key: str  # 仅在创建时返回完整key
    user_id: int
    is_active: bool
    last_used_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# API密钥列表响应（隐藏完整key）
class APIKeyListItem(BaseModel):
    """API密钥列表项Schema"""

    id: int
    name: str
    key_preview: str  # 只显示前8位
    is_active: bool
    expires_at: datetime | None
    last_used_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class APIKeyListResponse(BaseModel):
    """API密钥列表响应Schema"""

    total: int
    items: list[APIKeyListItem]
