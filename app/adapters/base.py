"""
@File    : base.py
@Author  : Martin
@Time    : 2025/11/4 11:11
@Desc    :
"""

from abc import ABC, abstractmethod
from app.schemas.chat import ChatCompletionResponse
from collections.abc import AsyncIterator
from enum import Enum
from pydantic import BaseModel

class ModelProvider(str, Enum):
    """模型供应商"""

    OPENAI = 'openai'
    CLAUDE = 'claude'
    ZHIPU = 'zhipu'
    QWEN = 'qwen'
    SILICONFLOW = 'siliconflow'


class ChatMessage(BaseModel):
    """聊天消息"""

    role: str  # system, user, assistant
    content: str
    name: str | None = None


class ChatRequest(BaseModel):
    """聊天请求"""

    model: str
    messages: list[ChatMessage]
    temperature: float = 0.7
    max_tokens: int | None = None
    stream: bool = False
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0


class ChatResponse(BaseModel):
    """聊天响应"""

    id: str
    model: str
    content: str
    finish_reason: str
    usage: dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    provider: ModelProvider


class StreamChunk(BaseModel):
    """流式响应块"""

    content: str
    finish_reason: str | None = None


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
    async def chat(self, request: ChatRequest) -> ChatCompletionResponse:
        """
        非流式聊天
        """
        pass

    @abstractmethod
    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """流式回答"""
        pass

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """
        获取可用模型列表
        """
        pass

    @abstractmethod
    def calculate_cost(self, usage: dict[str, int], model: str) -> float:
        """
        计算成本
        """
        pass

    def validate_request(self, request: ChatRequest) -> None:
        """验证请求参数"""
        if not request.messages:
            raise ValueError('Messages cannot be empty')

        if request.temperature < 0 or request.temperature > 2:
            raise ValueError('Temperature must be between 0 and 2')

        if request.model not in self.get_available_models():
            raise ValueError(f'Model {request.model} not supported')
