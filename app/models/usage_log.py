"""
@File    : usage_log.py.py
@Author  : Martin
@Time    : 2025/11/4 11:15
@Desc    : 使用记录模型
"""

from app.models.base import BaseModel
from sqlalchemy import JSON, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class UsageLog(BaseModel):
    """使用记录模型"""

    __tablename__ = 'usage_logs'
    __table_args__ = {'comment': '使用记录表'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment='记录ID')

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True, comment='用户ID'
    )

    conversation_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey('conversations.id', ondelete='SET NULL'), nullable=True, index=True, comment='对话ID'
    )

    model_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True, comment='模型名称')

    provider: Mapped[str] = mapped_column(String(50), nullable=False, index=True, comment='供应商')

    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment='输入Token数')

    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment='输出Token数')

    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False, comment='总Token数')

    cost: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment='成本(USD)')

    response_time: Mapped[float] = mapped_column(Float, default=0.0, nullable=False, comment='响应时间(秒)')

    # 修改这里：metadata -> extra_data
    extra_data: Mapped[dict | None] = mapped_column(JSON, nullable=True, comment='额外元数据')

    def __repr__(self) -> str:
        return f'<UsageLog(id={self.id}, user_id={self.user_id}, model={self.model_name})>'
