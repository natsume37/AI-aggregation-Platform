"""
@File    : api_key.py.py
@Author  : Martin
@Time    : 2025/11/1 22:48
@Desc    :
"""

from app.models.base import BaseModel
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User


class APIKey(BaseModel):
    """API密钥模型"""

    __tablename__ = 'api_keys'
    __table_args__ = {'comment': 'API密钥表'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment='密钥ID')

    key: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False, comment='API密钥')

    name: Mapped[str] = mapped_column(String(100), nullable=False, comment='密钥名称')

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment='所属用户ID'
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment='是否启用')

    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, comment='过期时间')

    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment='最后使用时间'
    )

    description: Mapped[str | None] = mapped_column(Text, nullable=True, comment='描述')

    # 关系
    user: Mapped['User'] = relationship('User', back_populates='api_keys')

    def __repr__(self) -> str:
        return f'<APIKey(id={self.id}, name={self.name}, user_id={self.user_id})>'
