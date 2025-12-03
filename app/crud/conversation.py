"""
@File    : conversation.py.py
@Author  : Martin
@Time    : 2025/11/4 11:19
@Desc    :
"""

from app.crud.base import CRUDBase
from app.models.conversation import Conversation
from app.models.message import Message
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


class ConversationCreate(BaseModel):
    """创建对话Schema"""

    api_key_id: int
    title: str
    model_name: str
    provider: str


class ConversationCRUD(CRUDBase[Conversation, ConversationCreate, BaseModel]):
    """对话CRUD操作"""

    async def get_by_api_key(self, db: AsyncSession, api_key_id: int, skip: int = 0, limit: int = 100) -> list[Conversation]:
        """获取API Key的对话列表"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.api_key_id == api_key_id)
            .order_by(Conversation.updated_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_with_messages(
        self, db: AsyncSession, conversation_id: int, api_key_id: int | None = None
    ) -> Conversation | None:
        """获取对话及其消息"""
        query = (
            select(Conversation).options(selectinload(Conversation.messages)).where(Conversation.id == conversation_id)
        )

        if api_key_id:
            query = query.where(Conversation.api_key_id == api_key_id)

        result = await db.execute(query)
        return result.scalar_one_or_none()

    async def count_by_api_key(self, db: AsyncSession, api_key_id: int) -> int:
        """统计API Key对话数"""
        result = await db.execute(select(func.count()).select_from(Conversation).where(Conversation.api_key_id == api_key_id))
        return result.scalar_one()

    async def add_message(
        self, db: AsyncSession, conversation_id: int, role: str, content: str, tokens: int = 0
    ) -> Message:
        """添加消息到对话"""
        message = Message(conversation_id=conversation_id, role=role, content=content, tokens=tokens)
        db.add(message)
        await db.flush()
        await db.refresh(message)
        return message

    async def get_messages(self, db: AsyncSession, conversation_id: int, limit: int | None = None) -> list[Message]:
        """获取对话消息"""
        query = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.asc())

        if limit:
            query = query.limit(limit)

        result = await db.execute(query)
        return list(result.scalars().all())


# 全局实例 - 确保这行存在！
conversation_crud = ConversationCRUD(Conversation)
