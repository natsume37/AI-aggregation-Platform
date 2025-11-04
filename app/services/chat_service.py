# -*- coding: utf-8 -*-
"""
@File    : chat_service.py.py
@Author  : Martin
@Time    : 2025/11/4 11:20
@Desc    : 
"""
import time
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.adapters.base import (
    ChatRequest,
    ChatMessage,
    ModelProvider
)
from app.adapters.model_registry import model_registry
from app.crud.conversation import conversation_crud, ConversationCreate
from app.crud.usage_log import usage_log_crud, UsageLogCreate
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.logging import log


class ChatService:
    """聊天服务"""

    async def chat(
            self,
            db: AsyncSession,
            user_id: int,
            model: str,
            messages: List[ChatMessage],
            conversation_id: Optional[int] = None,
            save_conversation: bool = True,
            **kwargs
    ) -> dict:
        """
        执行聊天

        Args:
            db: 数据库会话
            user_id: 用户ID
            model: 模型名称
            messages: 消息列表
            conversation_id: 对话ID（可选）
            save_conversation: 是否保存对话
            **kwargs: 其他参数（temperature, max_tokens等）

        Returns:
            包含响应和元数据的字典
        """
        start_time = time.time()

        # 1. 确定provider（这里简化处理，实际应该从配置或模型名称推断）
        provider = self._get_provider_from_model(model)

        # 2. 获取适配器
        adapter = model_registry.get_adapter(provider)

        # 3. 如果有conversation_id，加载历史消息
        if conversation_id:
            conversation = await conversation_crud.get_with_messages(
                db, conversation_id, user_id
            )
            if not conversation:
                raise ValueError("Conversation not found")

            # 合并历史消息（取最近N条）
            history_messages = await conversation_crud.get_messages(
                db, conversation_id, limit=10
            )

            # 转换为ChatMessage格式
            historical = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in history_messages
            ]

            # 合并消息
            all_messages = historical + messages
        else:
            all_messages = messages
            conversation = None

        # 4. 构建请求
        chat_request = ChatRequest(
            model=model,
            messages=all_messages,
            stream=False,
            **kwargs
        )

        # 5. 调用AI模型
        try:
            response = await adapter.chat(chat_request)
        except Exception as e:
            log.error(f"AI model error: {str(e)}")
            raise

        # 6. 计算响应时间
        response_time = time.time() - start_time

        # 7. 计算成本
        cost = adapter.calculate_cost(response.usage, model)

        # 8. 保存对话（如果需要）
        if save_conversation:
            if not conversation:
                # 创建新对话
                conversation = await self._create_conversation(
                    db, user_id, model, provider, messages[0].content[:50]
                )

            # 保存用户消息
            for msg in messages:
                await conversation_crud.add_message(
                    db, conversation.id, msg.role, msg.content
                )

            # 保存AI响应
            await conversation_crud.add_message(
                db,
                conversation.id,
                "assistant",
                response.content,
                response.usage["completion_tokens"]
            )

        # 9. 记录使用情况
        await self._log_usage(
            db,
            user_id,
            conversation.id if conversation else None,
            model,
            provider.value,
            response.usage,
            cost,
            response_time
        )

        # 10. 提交事务
        await db.commit()

        # 11. 返回结果
        return {
            "id": response.id,
            "conversation_id": conversation.id if conversation else None,
            "model": response.model,
            "provider": response.provider.value,
            "content": response.content,
            "finish_reason": response.finish_reason,
            "usage": response.usage,
            "cost": cost,
            "response_time": response_time
        }

    async def chat_stream(
            self,
            db: AsyncSession,
            user_id: int,
            model: str,
            messages: List[ChatMessage],
            conversation_id: Optional[int] = None,
            save_conversation: bool = True,
            **kwargs
    ):
        """
        流式聊天

        返回异步生成器
        """
        start_time = time.time()

        # 1. 获取适配器
        provider = self._get_provider_from_model(model)
        adapter = model_registry.get_adapter(provider)

        # 2. 加载历史消息（如果有）
        if conversation_id:
            conversation = await conversation_crud.get_with_messages(
                db, conversation_id, user_id
            )
            if not conversation:
                raise ValueError("Conversation not found")

            history_messages = await conversation_crud.get_messages(
                db, conversation_id, limit=10
            )

            historical = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in history_messages
            ]

            all_messages = historical + messages
        else:
            all_messages = messages
            conversation = None

        # 3. 构建请求
        chat_request = ChatRequest(
            model=model,
            messages=all_messages,
            stream=True,
            **kwargs
        )

        # 4. 流式调用
        full_content = ""
        finish_reason = None

        try:
            async for chunk in adapter.chat_stream(chat_request):
                if chunk.content:
                    full_content += chunk.content
                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason

                # 生成流式数据
                yield {
                    "content": chunk.content,
                    "finish_reason": chunk.finish_reason
                }

        except Exception as e:
            log.error(f"Streaming error: {str(e)}")
            raise

        # 5. 流式结束后保存（在后台任务中执行）
        response_time = time.time() - start_time

        # 简化的token计算（实际应该更精确）
        prompt_tokens = sum(len(msg.content) // 4 for msg in all_messages)
        completion_tokens = len(full_content) // 4
        total_tokens = prompt_tokens + completion_tokens

        usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens
        }

        cost = adapter.calculate_cost(usage, model)

        # 保存对话和使用记录
        if save_conversation:
            if not conversation:
                conversation = await self._create_conversation(
                    db, user_id, model, provider, messages[0].content[:50]
                )

            for msg in messages:
                await conversation_crud.add_message(
                    db, conversation.id, msg.role, msg.content
                )

            await conversation_crud.add_message(
                db, conversation.id, "assistant", full_content, completion_tokens
            )

        await self._log_usage(
            db,
            user_id,
            conversation.id if conversation else None,
            model,
            provider.value,
            usage,
            cost,
            response_time
        )

        await db.commit()

        # 最后发送元数据
        yield {
            "type": "metadata",
            "conversation_id": conversation.id if conversation else None,
            "usage": usage,
            "cost": cost,
            "response_time": response_time
        }

    def _get_provider_from_model(self, model: str) -> ModelProvider:
        """从模型名称推断provider"""
        if "gpt" in model.lower():
            return ModelProvider.OPENAI
        elif "claude" in model.lower():
            return ModelProvider.CLAUDE
        elif any(keyword in model.lower()for keyword in [
            "qwen", "deepseek", "glm", "llama", "sflow", "silicon", "siliconflow"
        ]):
            return ModelProvider.SILICONFLOW
        # 添加更多判断...

        # 默认返回OpenAI
        return ModelProvider.OPENAI

    async def _create_conversation(
            self,
            db: AsyncSession,
            user_id: int,
            model: str,
            provider: ModelProvider,
            title: str
    ) -> Conversation:
        """创建新对话"""
        conversation_data = ConversationCreate(
            user_id=user_id,
            title=title or "New Conversation",
            model_name=model,
            provider=provider.value
        )

        conversation = await conversation_crud.create(db, conversation_data)
        await db.flush()
        await db.refresh(conversation)

        return conversation

    async def _log_usage(
            self,
            db: AsyncSession,
            user_id: int,
            conversation_id: Optional[int],
            model: str,
            provider: str,
            usage: dict,
            cost: float,
            response_time: float
    ):
        """记录使用情况"""
        log_data = UsageLogCreate(
            user_id=user_id,
            conversation_id=conversation_id,
            model_name=model,
            provider=provider,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"],
            cost=cost,
            response_time=response_time
        )

        await usage_log_crud.create(db, log_data)


# 全局实例
chat_service = ChatService()