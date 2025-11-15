from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Any


class Base(DeclarativeBase):
    """基础模型类"""

    pass


class TimestampMixin:
    """时间戳混入类"""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, comment='创建时间'
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, comment='更新时间'
    )


class BaseModel(Base, TimestampMixin):
    """
    基础模型
    所有模型都应该继承此类
    """

    __abstract__ = True

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}
