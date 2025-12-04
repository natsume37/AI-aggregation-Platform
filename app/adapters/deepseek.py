"""
@File    : deepseek.py
@Author  : Martin
@Time    : 2025/11/12 16:37
@Desc    :
"""

import httpx
import json
from app.adapters.base import BaseLLMAdapter, ChatRequest, ChatResponse, ModelProvider, ModelRequestError, StreamChunk
from app.core.config import settings
import logging
from collections.abc import AsyncIterator

log = logging.getLogger("app")


class DeepSeekerAdapter(BaseLLMAdapter):
    """Deepseek adapter"""

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or 'https://api.deepseek.com'
        self.provider = ModelProvider.DEEPSEEK

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
            timeout=settings.CONNECT_TIMEOUT,
        )

    def _build_payload(self, request: ChatRequest, is_stream: bool = False) -> dict:
        """构建请求 payload"""
        return {
            'model': request.model,
            'messages': [msg.model_dump(exclude_none=True) for msg in request.messages],
            'temperature': request.temperature,
            'max_tokens': request.max_tokens,
            'top_p': request.top_p,
            'frequency_penalty': request.frequency_penalty,
            'presence_penalty': request.presence_penalty,
            'stream': is_stream,
        }

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """
        非流式聊天
        """
        await self.validate_request(request)
        # 构建请求体
        payload = self._build_payload(request, is_stream=False)

        try:
            async with await self._get_client() as client:
                response = await client.post('/chat/completions', json=payload)
                response.raise_for_status()
                data = response.json()

            choice = data['choices'][0]
            message = choice['message']
            # print('deepseek', data)
            # 兼容适配器：usage = {prompt_tokens, completion_tokens, total_tokens}
            raw_usage = data.get('usage', {})
            filtered_usage = {
                'prompt_tokens': raw_usage.get('prompt_tokens', 0),
                'completion_tokens': raw_usage.get('completion_tokens', 0),
                'total_tokens': raw_usage.get('total_tokens', 0),
            }
            return ChatResponse(
                id=data.get('id', ''),
                model=data.get('model', request.model),
                content=message.get('content', ''),
                finish_reason=choice.get('finish_reason', ''),
                usage=filtered_usage,
                provider=self.provider,
            )

        except httpx.HTTPStatusError as e:
            log.error(f'DeepSeek API error: {e.response.status_code} - {e.response.text}')
            raise Exception(f'DeepSeek API error: {e.response.text}')
        except Exception as e:
            log.error(f'Unexpected DeepSeek error: {str(e)}')
            raise ModelRequestError(str(e))

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """流式回答"""
        await self.validate_request(request)

        payload = self._build_payload(request, is_stream=True)

        try:
            async with await self._get_client() as client:
                async with client.stream('POST', '/chat/completions', json=payload) as response:
                    response.raise_for_status()

                    # 按行读取 SSE 流
                    async for line in response.aiter_lines():
                        line = line.strip()

                        # 跳过空行和注释
                        if not line or line.startswith(':'):
                            continue

                        # 解析 "data: " 前缀
                        if line.startswith('data: '):
                            data = line[6:]  # 去掉 "data: " 前缀

                            # 流结束标志
                            if data == '[DONE]':
                                break

                            try:
                                chunk = json.loads(data)
                                delta = chunk['choices'][0].get('delta', {})

                                if 'content' in delta:
                                    yield StreamChunk(
                                        content=delta['content'], finish_reason=chunk['choices'][0].get('finish_reason')
                                    )

                                # 最后一个 chunk 可能包含 usage
                                if 'usage' in chunk:
                                    # 可以选择性地处理 usage
                                    pass

                            except json.JSONDecodeError:
                                continue

        except httpx.HTTPStatusError as e:
            log.error(f'DeepSeek API error: {e.response.status_code} - {e.response.text}')
            raise
        except Exception as e:
            log.error(f'Unexpected DeepSeek error: {str(e)}')
            raise

    async def get_available_models(self) -> list[str]:
        """
        获取可用模型列表
        """
        async with await self._get_client() as client:
            res = await client.get('/models')
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
        pass
