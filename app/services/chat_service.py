"""
@File    : chat_service.py.py
@Author  : Martin
@Time    : 2025/11/4 11:20
@Desc    :
"""

import time
from typing import Optional, List, Union
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import ModelProvider
from app.adapters.base import BaseLLMAdapter, ChatMessage, ChatRequest  # ← 适配器的类
from app.adapters.model_registry import model_registry
from app.main import log
from app.crud.conversation import ConversationCreate, conversation_crud
from app.crud.usage_log import UsageLogCreate, usage_log_crud
from app.models.conversation import Conversation
from app.schemas.chat import ChatMessageRequest  # ← API 层的类


class ChatService:
    """聊天服务"""

    async def chat(
            self,
            db: AsyncSession,
            user_id: int,
            model: str,
            messages: List[Union[ChatMessageRequest, ChatMessage, dict]],  # 支持多种类型
            conversation_id: Optional[int] = None,
            save_conversation: bool = True,
            provider: Optional[ModelProvider] = None,
            **kwargs,
    ) -> dict:
        """执行聊天"""
        start_time = time.time()

        # 1. 确定 provider
        if provider is None:
            provider = self._get_provider_from_model(model)

        # 2. 获取适配器
        adapter: BaseLLMAdapter = model_registry.get_adapter(provider)

        # 3. ✅ 转换消息格式为适配器需要的 ChatMessage
        chat_messages = self._convert_to_chat_messages(messages)

        # 4. 如果有 conversation_id，加载历史消息
        if conversation_id:
            conversation = await conversation_crud.get_with_messages(
                db, conversation_id, user_id
            )
            if not conversation:
                raise ValueError('Conversation not found')

            # 验证 provider 是否一致
            if conversation.provider != provider.value:
                log.warning(
                    f"Provider mismatch: conversation={conversation.provider}, "
                    f"request={provider.value}"
                )

            # 获取历史消息
            history_messages = await conversation_crud.get_messages(
                db, conversation_id, limit=10
            )
            historical = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in history_messages
            ]
            all_messages = historical + chat_messages  # ← 都是 ChatMessage 类型
        else:
            all_messages = chat_messages
            conversation = None

        # 5. ✅ 构建适配器请求（all_messages 已经是 List[ChatMessage]）
        chat_request = ChatRequest(
            model=model,
            messages=all_messages,  # ← 现在是正确的类型
            stream=False,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens'),
            top_p=kwargs.get('top_p', 1.0),
            frequency_penalty=kwargs.get('frequency_penalty', 0.0),
            presence_penalty=kwargs.get('presence_penalty', 0.0),
        )

        # 6. 调用 AI 模型
        try:
            response = await adapter.chat(chat_request)
        except Exception as e:
            log.error(f"AI model error: {str(e)}", exc_info=True)
            raise

        # 7. 计算响应时间
        response_time = time.time() - start_time

        # 8. 计算成本
        cost = adapter.calculate_cost(response.usage, model)

        # 9. 保存对话
        if save_conversation:
            if not conversation:
                conversation = await self._create_conversation(
                    db, user_id, model, provider, chat_messages[0].content[:50]
                )

            # 保存用户消息
            for msg in chat_messages:
                await conversation_crud.add_message(
                    db, conversation.id, msg.role, msg.content
                )

            # 保存 AI 响应
            await conversation_crud.add_message(
                db,
                conversation.id,
                'assistant',
                response.content,
                response.usage['completion_tokens']
            )

        # 10. 记录使用情况
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

        # 11. 提交事务
        await db.commit()

        # 12. 返回结果
        return {
            'id': response.id,
            'conversation_id': conversation.id if conversation else None,
            'model': response.model,
            'provider': response.provider.value,
            'content': response.content,
            'finish_reason': response.finish_reason,
            'usage': response.usage,
            'cost': cost,
            'response_time': response_time,
        }

    async def chat_stream(
            self,
            db: AsyncSession,
            user_id: int,
            model: str,
            messages: List[Union[ChatMessageRequest, ChatMessage, dict]],
            conversation_id: Optional[int] = None,
            save_conversation: bool = True,
            provider: Optional[ModelProvider] = None,
            **kwargs,
    ):
        """流式聊天"""
        start_time = time.time()

        # 1. 确定 provider
        if provider is None:
            provider = self._get_provider_from_model(model)

        # 2. 获取适配器
        adapter = model_registry.get_adapter(provider)

        # 3. ✅ 转换消息格式
        chat_messages = self._convert_to_chat_messages(messages)

        # 4. 加载历史消息（如果有）
        if conversation_id:
            conversation = await conversation_crud.get_with_messages(
                db, conversation_id, user_id
            )
            if not conversation:
                raise ValueError('Conversation not found')

            history_messages = await conversation_crud.get_messages(
                db, conversation_id, limit=10
            )
            historical = [
                ChatMessage(role=msg.role, content=msg.content)
                for msg in history_messages
            ]
            all_messages = historical + chat_messages
        else:
            all_messages = chat_messages
            conversation = None

        # 5. ✅ 构建请求
        chat_request = ChatRequest(
            model=model,
            messages=all_messages,  # ← 正确的类型
            stream=True,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens'),
            top_p=kwargs.get('top_p', 1.0),
            frequency_penalty=kwargs.get('frequency_penalty', 0.0),
            presence_penalty=kwargs.get('presence_penalty', 0.0),
        )

        # 6. 流式调用
        full_content = ''
        finish_reason = None

        try:
            async for chunk in adapter.chat_stream(chat_request):
                if chunk.content:
                    full_content += chunk.content
                if chunk.finish_reason:
                    finish_reason = chunk.finish_reason

                yield {
                    'content': chunk.content,
                    'finish_reason': chunk.finish_reason
                }

        except Exception as e:
            log.error(f'Streaming error: {str(e)}', exc_info=True)
            raise

        # ... 后续保存逻辑 ...

    def _convert_to_chat_messages(
            self,
            messages: List[Union[ChatMessageRequest, ChatMessage, dict]]
    ) -> List[ChatMessage]:
        """
        ✅ 转换不同格式的消息为适配器需要的 ChatMessage

        Args:
            messages: 可能是 ChatMessageRequest, ChatMessage 或 dict

        Returns:
            List[ChatMessage] - 适配器层的消息格式
        """
        chat_messages = []

        for msg in messages:
            if isinstance(msg, ChatMessage):
                # 已经是适配器的 ChatMessage，直接使用
                chat_messages.append(msg)

            elif isinstance(msg, ChatMessageRequest):
                # API 层的 ChatMessageRequest，转换为 ChatMessage
                chat_messages.append(
                    ChatMessage(
                        role=msg.role,
                        content=msg.content
                    )
                )

            elif hasattr(msg, 'role') and hasattr(msg, 'content'):
                # 类似对象（有 role 和 content 属性）
                chat_messages.append(
                    ChatMessage(
                        role=msg.role,
                        content=msg.content
                    )
                )

            elif isinstance(msg, dict):
                # 字典格式
                chat_messages.append(
                    ChatMessage(
                        role=msg['role'],
                        content=msg['content']
                    )
                )

            else:
                raise ValueError(f"Unsupported message type: {type(msg)}")

        return chat_messages

    def _get_provider_from_model(self, model: str) -> ModelProvider:
        """从模型名称推断 provider"""
        model_lower = model.lower()

        if 'gpt' in model_lower:
            return ModelProvider.OPENAI

        if 'deepseek' in model_lower:
            return ModelProvider.DEEPSEEK

        siliconflow_keywords = [
            'qwen', 'glm', 'llama',
            'sflow', 'silicon', 'siliconflow',
            'stepfun-ai', 'yi-', 'internlm'
        ]
        if any(keyword in model_lower for keyword in siliconflow_keywords):
            return ModelProvider.SILICONFLOW

        log.warning(f"Could not determine provider for model '{model}', defaulting to OPENAI")
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
            title=title or 'New Conversation',
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
            response_time: float,
    ):
        """记录使用情况"""
        log_data = UsageLogCreate(
            user_id=user_id,
            conversation_id=conversation_id,
            model_name=model,
            provider=provider,
            prompt_tokens=usage['prompt_tokens'],
            completion_tokens=usage['completion_tokens'],
            total_tokens=usage['total_tokens'],
            cost=cost,
            response_time=response_time,
        )

        await usage_log_crud.create(db, log_data)


# 全局实例
chat_service = ChatService()
