# -*- coding: utf-8 -*-
"""
@File    : doubao.py
@Author  : Martin
@Time    : 2025/12/20 12:58
@Desc    : 豆包（火山引擎）模型适配器
"""

import httpx
import json
from fastapi import HTTPException
from collections.abc import AsyncIterator
from app.adapters.base import BaseLLMAdapter, ChatRequest, ChatResponse, ModelProvider, StreamChunk
from app.core.config import settings
import logging

log = logging.getLogger("app")


class DoubaoAdapter(BaseLLMAdapter):
    """豆包（火山引擎）API适配器"""

    # 模型定价 (仅供参考，实际需查阅火山引擎文档)
    MODEL_PRICING = {
        'doubao-pro-4k': {'prompt': 0.0008, 'completion': 0.002},
        'doubao-pro-32k': {'prompt': 0.0008, 'completion': 0.002},
        'doubao-lite-4k': {'prompt': 0.0003, 'completion': 0.0006},
        'doubao-lite-32k': {'prompt': 0.0003, 'completion': 0.0006},
        'doubao-1-5-vision-pro-32k-250115': {'prompt': 0.0008, 'completion': 0.002}, # 假设价格
    }

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or settings.DOUBAO_BASE_URL or 'https://ark.cn-beijing.volces.com/api/v3'
        self.provider = ModelProvider.DOUBAO

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
            timeout=settings.CONNECT_TIMEOUT,
        )

    async def get_available_models(self) -> list[str]:
        """获取可用模型列表"""
        # 这里可以返回硬编码的列表，或者调用 API 获取
        return list(self.MODEL_PRICING.keys())

    def calculate_cost(self, usage: dict[str, int], model: str) -> float:
        """计算成本（美元/人民币，需统一单位，这里假设是人民币或与OpenAI一致的单位）"""
        # 注意：火山引擎通常以人民币计费，这里仅做示例
        if model not in self.MODEL_PRICING:
            return 0.0

        pricing = self.MODEL_PRICING[model]
        prompt_cost = (usage.get('prompt_tokens', 0) / 1000) * pricing['prompt']
        completion_cost = (usage.get('completion_tokens', 0) / 1000) * pricing['completion']

        return prompt_cost + completion_cost

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """非流式聊天"""
        await self.validate_request(request)

        # 构建请求体
        payload = {
            'model': request.model,
            'messages': [msg.model_dump(exclude_none=True) for msg in request.messages],
            'temperature': request.temperature,
            'top_p': request.top_p,
            'frequency_penalty': request.frequency_penalty,
            'presence_penalty': request.presence_penalty,
            'stream': False,
        }

        if request.max_tokens:
            payload['max_tokens'] = request.max_tokens

        try:
            async with await self._get_client() as client:
                # 火山引擎兼容 OpenAI 接口
                response = await client.post('/chat/completions', json=payload)
                response.raise_for_status()
                data = response.json()

            # 解析响应
            choice = data['choices'][0]
            message = choice['message']

            usage = data.get('usage') or {}
            usage_simple = {
                'prompt_tokens': int(usage.get('prompt_tokens') or 0),
                'completion_tokens': int(usage.get('completion_tokens') or 0),
                'total_tokens': int(usage.get('total_tokens') or 0),
            }

            return ChatResponse(
                id=data['id'],
                model=data['model'],
                content=message['content'],
                finish_reason=choice['finish_reason'],
                usage=usage_simple,
                provider=self.provider,
            )

        except httpx.HTTPStatusError as e:
            log.error(f'Doubao API error: {e.response.status_code} - {e.response.text}')
            raise HTTPException(status_code=e.response.status_code, detail=f'Doubao API error: {e.response.text}')
        except Exception as e:
            log.error(f'Unexpected error: {str(e)}')
            raise

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """流式聊天"""
        await self.validate_request(request)

        # 构建请求体
        payload = {
            'model': request.model,
            'messages': [msg.model_dump(exclude_none=True) for msg in request.messages],
            'temperature': request.temperature,
            'top_p': request.top_p,
            'frequency_penalty': request.frequency_penalty,
            'presence_penalty': request.presence_penalty,
            'stream': True,
        }

        if request.max_tokens:
            payload['max_tokens'] = request.max_tokens

        try:
            async with await self._get_client() as client:
                async with client.stream('POST', '/chat/completions', json=payload) as response:
                    response.raise_for_status()

                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue

                        if line.startswith('data: '):
                            data_str = line[6:]

                            if data_str == '[DONE]':
                                break

                            try:
                                data = json.loads(data_str)
                                choice = data['choices'][0]
                                delta = choice.get('delta', {})

                                if 'content' in delta:
                                    yield StreamChunk(content=delta['content'], finish_reason=None)

                                if choice.get('finish_reason'):
                                    yield StreamChunk(content='', finish_reason=choice['finish_reason'])

                            except json.JSONDecodeError:
                                continue

        except httpx.HTTPStatusError as e:
            log.error(f'Doubao streaming error: {e.response.status_code}')
            raise HTTPException(status_code=e.response.status_code, detail=f'Doubao streaming error: {e.response.text}')
        except Exception as e:
            log.error(f'Unexpected streaming error: {str(e)}')
            raise
