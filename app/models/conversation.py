"""
@File    : conversation.py.py
@Author  : Martin
@Time    : 2025/11/4 11:14
@Desc    : 对话数据库模型
"""

from app.models.base import BaseModel
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.message import Message
    from app.models.api_key import APIKey


class Conversation(BaseModel):
    """对话模型"""

    __tablename__ = 'conversations'
    __table_args__ = {'comment': '对话表'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment='对话ID')

    api_key_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('api_keys.id', ondelete='CASCADE'), nullable=False, index=True, comment='API Key ID'
    )

    title: Mapped[str] = mapped_column(String(200), nullable=False, comment='对话标题')

    model_name: Mapped[str] = mapped_column(String(100), nullable=False, comment='使用的模型')

    provider: Mapped[str] = mapped_column(String(50), nullable=False, comment='模型供应商')

    # 关系
    api_key: Mapped['APIKey'] = relationship('APIKey', back_populates='conversations')
    messages: Mapped[list['Message']] = relationship(
        'Message', back_populates='conversation', cascade='all, delete-orphan', order_by='Message.created_at'
    )

    def __repr__(self) -> str:
        return f'<Conversation(id={self.id}, title={self.title}, api_key_id={self.api_key_id})>'
