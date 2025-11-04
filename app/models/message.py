# -*- coding: utf-8 -*-
"""
@File    : message.py.py
@Author  : Martin
@Time    : 2025/11/4 11:15
@Desc    : 消息数据库模型
"""
from typing import TYPE_CHECKING
from sqlalchemy import String, Integer, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class Message(BaseModel):
    """消息模型"""

    __tablename__ = "messages"
    __table_args__ = {"comment": "消息表"}

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
        comment="消息ID"
    )

    conversation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="对话ID"
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="角色: system/user/assistant"
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="消息内容"
    )

    tokens: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Token数量"
    )

    # 关系
    conversation: Mapped["Conversation"] = relationship(
        "Conversation",
        back_populates="messages"
    )

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, role={self.role}, conversation_id={self.conversation_id})>"