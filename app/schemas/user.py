from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# 基础Schema
class UserBase(BaseModel):
    """用户基础Schema"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")


# 创建用户Schema
class UserCreate(UserBase):
    """创建用户Schema"""
    password: str = Field(..., min_length=6, max_length=50, description="密码")


# 更新用户Schema
class UserUpdate(BaseModel):
    """更新用户Schema"""
    email: Optional[EmailStr] = Field(None, description="邮箱")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    password: Optional[str] = Field(None, min_length=6, max_length=50, description="密码")
    is_active: Optional[bool] = Field(None, description="是否激活")


# 响应Schema
class UserResponse(UserBase):
    """用户响应Schema"""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 用户列表Schema
class UserListResponse(BaseModel):
    """用户列表响应Schema"""
    total: int
    items: list[UserResponse]