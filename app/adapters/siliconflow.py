"""
@File    : siliconflow.py
@Author  : Martin
@Desc    : SiliconFlow API 适配器
"""

import httpx
import json
from app.adapters.base import BaseLLMAdapter, ChatRequest, ChatResponse, StreamChunk
from app.core.config import settings
from app.core.enums import ModelProvider
from app.main import log
from collections.abc import AsyncIterator


class SiliconFlowAdapter(BaseLLMAdapter):
    """SiliconFlow API 适配器"""

    # 模型定价（如果有的话，根据实际情况调整）
    MODEL_PRICING = {
        'deepseek-ai/deepseek-v3': {'prompt': 0.0001, 'completion': 0.0002},
        'qwen/qwen-turbo': {'prompt': 0.0001, 'completion': 0.0002},
    }

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or 'https://api.siliconflow.cn/v1'
        self.provider = ModelProvider.SILICONFLOW
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
            timeout=settings.CONNECT_TIMEOUT,
        )

    async def get_available_models(self) -> list[str]:
        """获取可用模型（异步方法）"""

        try:
            # 使用 self.client 异步发送 GET 请求
            response = await self.client.get('/models')
            response.raise_for_status()
            data = response.json()

            # 提取 id 列表
            model_ids = [item['id'] for item in data.get('data', [])]
            return model_ids

        except httpx.HTTPStatusError as e:
            raise Exception(f'API 请求失败: {e.response.status_code} - {e.response.text}') from e
        except Exception as e:
            raise Exception(f'未知错误: {str(e)}') from e

    def calculate_cost(self, usage: dict[str, int], model: str) -> float:
        """计算成本"""
        if model not in self.MODEL_PRICING:
            # 如果没有定价信息，返回0或使用默认定价
            log.warning(f'No pricing info for model: {model}')
            return 0.0

        pricing = self.MODEL_PRICING[model]
        prompt_cost = (usage.get('prompt_tokens', 0) / 1000) * pricing['prompt']
        completion_cost = (usage.get('completion_tokens', 0) / 1000) * pricing['completion']

        return prompt_cost + completion_cost

    def _build_payload(self, request: ChatRequest, is_stream: bool = False) -> dict:
        return {
            'model': request.model,
            'messages': [msg.model_dump(exclude_none=True) for msg in request.messages],
            'temperature': request.temperature,
            'top_p': request.top_p,
            'frequency_penalty': request.frequency_penalty,
            'presence_penalty': request.presence_penalty,
            'stream': is_stream,
        }

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """非流式聊天"""
        await self.validate_request(request)

        # ✅ 构建请求体 - 只包含 API 需要的字段
        payload = self._build_payload(request, is_stream=False)

        if request.max_tokens:
            payload['max_tokens'] = request.max_tokens

        try:
            log.debug(f'Sending request to SiliconFlow: {payload}')

            response = await self.client.post('/chat/completions', json=payload)
            response.raise_for_status()
            data = response.json()

            # 解析响应
            choice = data['choices'][0]
            message = choice['message']
            print(data)
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
            log.error(f'SiliconFlow API error: {e.response.status_code} - {e.response.text}')
            raise ModuleNotFoundError(f'SiliconFlow API error: {e.response.text}')
        except Exception as e:
            log.error(f'Unexpected error: {str(e)}')
            raise ModuleNotFoundError(str(e))

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """流式聊天"""
        await self.validate_request(request)

        # 构建请求体
        payload = self._build_payload(request, is_stream=True)

        if request.max_tokens:
            payload['max_tokens'] = request.max_tokens

        try:
            async with self.client.stream('POST', '/chat/completions', json=payload) as response:
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
            log.error(f'SiliconFlow streaming error: {e.response.status_code}')
            raise Exception(f'SiliconFlow streaming error: {e.response.text}')
        except Exception as e:
            log.error(f'Unexpected streaming error: {str(e)}')
            raise

    async def close(self):
        """关闭客户端"""

        await self.client.aclose()
