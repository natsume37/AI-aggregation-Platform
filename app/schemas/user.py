from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# 基础Schema
class UserBase(BaseModel):
    """用户基础Schema"""

    username: str = Field(..., min_length=3, max_length=50, description='用户名')
    email: EmailStr = Field(..., description='邮箱')
    full_name: str | None = Field(None, max_length=100, description='全名')


# 创建用户Schema
class UserCreate(UserBase):
    """创建用户Schema"""

    password: str = Field(..., min_length=4, max_length=50, description='密码')
    is_superuser: bool = False
    is_active: bool = True
    is_admin: bool = False
    must_change_password: bool = False


# 更新用户Schema
class UserUpdate(BaseModel):
    """更新用户Schema"""

    email: EmailStr | None = Field(None, description='邮箱')
    full_name: str | None = Field(None, max_length=100, description='全名')
    password: str | None = Field(None, min_length=6, max_length=50, description='密码')
    is_active: bool | None = Field(None, description='是否激活')
    must_change_password: bool | None = Field(None, description='是否必须修改密码')


# 修改密码Schema
class UserPasswordUpdate(BaseModel):
    """修改密码Schema"""
    
    old_password: str = Field(..., min_length=1, description='旧密码')
    new_password: str = Field(..., min_length=4, max_length=50, description='新密码')


# 响应Schema
class UserResponse(UserBase):
    """用户响应Schema"""

    id: int
    is_active: bool
    is_superuser: bool
    must_change_password: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 用户列表Schema
class UserListResponse(BaseModel):
    """用户列表响应Schema"""

    total: int
    items: list[UserResponse]
