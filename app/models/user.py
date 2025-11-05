from app.models.base import BaseModel
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.api_key import APIKey
# 在文件开头的导入部分
if TYPE_CHECKING:
    from app.models.api_key import APIKey
    from app.models.conversation import Conversation  # 新增


class User(BaseModel):
    """用户模型"""

    __tablename__ = 'users'
    __table_args__ = {'comment': '用户表'}

    id: Mapped[int] = mapped_column(primary_key=True, index=True, comment='用户ID')

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False, comment='用户名')

    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False, comment='邮箱')

    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False, comment='密码哈希')

    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment='全名')

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment='是否激活')

    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, comment='是否超级用户')

    # 关系
    api_keys: Mapped[list['APIKey']] = relationship('APIKey', back_populates='user', cascade='all, delete-orphan')
    conversations: Mapped[list['Conversation']] = relationship(
        'Conversation', back_populates='user', cascade='all, delete-orphan'
    )

    def __repr__(self) -> str:
        return f'<User(id={self.id}, username={self.username}, email={self.email})>'
