# -*- coding: utf-8 -*-
"""
@File    : deepseek.py
@Author  : Martin
@Time    : 2025/11/12 16:37
@Desc    : 
"""
from typing import AsyncIterator

import httpx
from app.adapters.base import BaseLLMAdapter, ChatRequest, ChatResponse, ModelProvider, StreamChunk
from app.schemas.chat import ChatCompletionResponse


# client = OpenAI(api_key='sk-febde2dc64474e25993c7728b2f2bed8', base_url="https://api.deepseek.com")
#
# response = client.chat.completions.create(
#     model="deepseek-chat",
#     messages=[
#         {"role": "system", "content": "You are a helpful assistant"},
#         {"role": "user", "content": "Hello"},
#     ],
#     stream=False
# )
#
# print(response.choices[0].message.content)


class DeepSeekerAdapter(BaseLLMAdapter):
    """Deepseek adapter"""

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or 'https://api.deepseek.com'
        self.provider = ModelProvider.OPENAI
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
            timeout=60.0,
        )

    async def chat(self, request: ChatRequest) -> ChatCompletionResponse:
        """
        非流式聊天
        """

        pass

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
        return data['data']

    def calculate_cost(self, usage: dict[str, int], model: str) -> float:
        """
        计算成本
        """
        pass

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


if __name__ == '__main__':
    import os
    import asyncio


    async def main():
        api_key = 'sk-febde2dc64474e25993c7728b2f2bed8'
        adapter = DeepSeekerAdapter(api_key=api_key)
        try:
            print("正在获取 DeepSeek 模型列表...")
            models = await adapter.get_available_models()
            print(models)
        except Exception as e:
            print(f"请求失败: {e}")
        finally:
            await adapter.close()


    asyncio.run(main())
