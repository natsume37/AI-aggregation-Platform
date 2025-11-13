# -*- coding: utf-8 -*-
"""
@File    : deepseek.py
@Author  : Martin
@Time    : 2025/11/12 16:37
@Desc    : 
"""
from typing import AsyncIterator, Any, Coroutine

import httpx
from app.adapters.base import BaseLLMAdapter, ChatRequest, ModelProvider, StreamChunk, ChatResponse
from app.core.config import settings
from app.main import log


class DeepSeekerAdapter(BaseLLMAdapter):
    """Deepseek adapter"""

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or 'https://api.deepseek.com'
        self.provider = ModelProvider.DEEPSEEK
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
            timeout=60.0,
        )

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        非流式聊天
        """
        await self.validate_request(request)

        # 构建请求体
        payload = {
            "model": request.model,
            "messages": [msg.model_dump(exclude_none=True) for msg in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": False,
        }

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data["choices"][0]
            message = choice["message"]
            # print('deepseek', data)
            # 兼容适配器：usage = {prompt_tokens, completion_tokens, total_tokens}
            raw_usage = data.get("usage", {})
            filtered_usage = {
                "prompt_tokens": raw_usage.get("prompt_tokens", 0),
                "completion_tokens": raw_usage.get("completion_tokens", 0),
                "total_tokens": raw_usage.get("total_tokens", 0)
            }
            return ChatResponse(
                id=data.get("id", ""),
                model=data.get("model", request.model),
                content=message.get("content", ""),
                finish_reason=choice.get("finish_reason", ""),
                usage=filtered_usage,
                provider=self.provider,
            )

        except httpx.HTTPStatusError as e:
            log.error(f"DeepSeek API error: {e.response.status_code} - {e.response.text}")
            raise Exception(f"DeepSeek API error: {e.response.text}")
        except Exception as e:
            log.error(f"Unexpected DeepSeek error: {str(e)}")
            raise

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """流式回答"""
        pass

    async def get_available_models(self) -> list[str]:
        """
        获取可用模型列表
        """
        res = await self.client.get('/models')
        res.raise_for_status()
        data = res.json()

        return [id['id'] for id in data['data']]

    def calculate_cost(self, usage: dict[str, int], model: str) -> float:
        """
        计算成本
        """
        return float(0)

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
