"""
@File    : base.py
@Author  : Martin
@Time    : 2025/11/4 11:11
@Desc    : 适配器基类（适配器层独立使用）
"""
import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from pydantic import BaseModel

from app.core.config import settings
from app.core.enums import ModelProvider


# ==================== 适配器层的数据模型 ====================

class ChatMessage(BaseModel):
    """聊天消息（适配器层）"""
    role: str  # system, user, assistant
    content: str
    name: str | None = None


class ChatRequest(BaseModel):
    """聊天请求（适配器层）"""
    model: str
    messages: list[ChatMessage]  # ← 注意这里是 ChatMessage，不是 ChatMessageRequest
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class ChatResponse(BaseModel):
    """聊天响应（适配器层）"""
    id: str
    model: str
    content: str
    finish_reason: str
    usage: dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    provider: ModelProvider  # ← 枚举


class StreamChunk(BaseModel):
    """流式响应块"""
    content: str
    finish_reason: str | None = None


def inject_system_prompt(messages: list[ChatMessage]) -> list[ChatMessage]:
    """在适配器层消息列表前插入系统提示词"""
    system_message = ChatMessage(
        role="system",
        content=settings.SYSTEM_PROMPT
    )
    return [system_message, *messages]


# ==================== 适配器抽象基类 ====================

class BaseLLMAdapter(ABC):
    """
    LLM适配器抽象基类
    所有模型适配器都必须继承此类
    """

    def __init__(self, api_key: str, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url
        self.provider: ModelProvider = ModelProvider.OPENAI

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        """非流式聊天"""
        pass

    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """流式聊天"""
        pass

    @abstractmethod
    async def get_available_models(self) -> list[str]:
        """获取可用模型列表（同步方法）"""
        pass

    @abstractmethod
    def calculate_cost(self, usage: dict[str, int], model: str) -> float:
        """计算成本"""
        pass

    async def validate_request(self, request: ChatRequest) -> None:
        """验证请求参数"""
        if not request.messages:
            raise ValueError('Messages cannot be empty')

        if request.temperature < 0 or request.temperature > 2:
            raise ValueError('Temperature must be between 0 and 2')

        available_models = await self.get_available_models()
        if request.model not in available_models:
            raise ValueError(
                f"Model '{request.model}' not supported by {self.provider.value}. "
                f"Available models: {available_models}"
            )


class ModelFetchError(Exception):
    """自定义模型获取错误"""
    pass

class ModelRequestError(Exception):
    """自定义模型请求错误"""
    pass