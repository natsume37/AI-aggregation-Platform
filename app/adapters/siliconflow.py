"""
@File    : silicon_flow.py
@Author  : Martin
@Time    : 2025/11/4 11:10
@Desc    :
"""

import httpx
import json
import time
from app.adapters.base import BaseLLMAdapter, ChatRequest, ModelFetchError, ModelProvider, StreamChunk
from app.core.logging import log
from app.schemas.chat import ChatCompletionResponse, CompletionTokensDetails, UsageInfo
from collections.abc import AsyncIterator
from datetime import datetime

class SiliconFlow(BaseLLMAdapter):
    """OpenAI API适配器"""

    # 模型定价 (USD per 1K tokens)
    MODEL_PRICING = {
        'deepseek-ai/DeepSeek-V3': {'prompt': 0.03, 'completion': 0.06},
        'deepseek-ai/DeepSeek-V3.1': {'prompt': 0.01, 'completion': 0.03},
        'deepseek-ai/DeepSeek-R1-Distill-Qwen-7B': {'prompt': 0.0005, 'completion': 0.0015},
        'stepfun-ai/step3': {'prompt': 0.003, 'completion': 0.004},
    }

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or 'https://api.siliconflow.cn/v1'
        self.provider = ModelProvider.SILICONFLOW
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
            timeout=60.0,
        )

    def get_available_models(self) -> list[str]:
        """获取可用模型列表"""
        """从 SiliconFlow API 实时获取模型列表并打印"""
        url = f'{self.base_url}/models'
        headers = {'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'}

        try:
            response = httpx.get(url, headers=headers, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            model_ids = [item['id'].lower() for item in data['data']]
            return model_ids
        except httpx.HTTPStatusError as e:
            raise ModelFetchError(f'API 请求失败: {e.response.status_code}') from e
        except Exception as e:
            raise ModelFetchError(f'未知错误: {str(e)}') from e

    def calculate_cost(self, usage: dict[str, int], model: str) -> float:
        """计算成本"""
        if model not in self.MODEL_PRICING:
            return 0.0

        pricing = self.MODEL_PRICING[model]
        prompt_cost = (usage.get('prompt_tokens', 0) / 1000) * pricing['prompt']
        completion_cost = (usage.get('completion_tokens', 0) / 1000) * pricing['completion']

        return prompt_cost + completion_cost

    async def chat(self, request: ChatRequest) -> ChatCompletionResponse:  # 返回你的新模型
        self.validate_request(request)

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

        start_time = time.time()

        try:
            response = await self.client.post('/chat/completions', json=payload)
            response.raise_for_status()
            data = response.json()

            choice = data['choices'][0]
            message = choice['message']

            # 安全解析 usage
            raw_usage = data.get('usage', {})
            completion_details = raw_usage.get('completion_tokens_details')

            usage = UsageInfo(
                prompt_tokens=raw_usage.get('prompt_tokens', 0),
                completion_tokens=raw_usage.get('completion_tokens', 0),
                total_tokens=raw_usage.get('total_tokens', 0),
                completion_tokens_details=CompletionTokensDetails(**completion_details) if completion_details else None,
            )

            # 计算成本
            cost = self.calculate_cost(
                usage={'prompt_tokens': usage.prompt_tokens, 'completion_tokens': usage.completion_tokens},
                model=request.model,
            )

            # 返回你的新模型
            return ChatCompletionResponse(
                id=data['id'],
                conversation_id=request.conversation_id or 0,  # 你需要从 request 或 DB 获取
                model=data['model'],
                provider=self.provider.value,  # 枚举转 str
                content=message['content'],
                finish_reason=choice['finish_reason'],
                usage=usage,
                cost=cost,
                response_time=time.time() - start_time,
                created_at=datetime.utcnow(),
            )

        except httpx.HTTPStatusError as e:
            log.error(f'siliconflow API error: {e.response.status_code} - {e.response.text}')
            raise
        except Exception as e:
            log.error(f'Unexpected error: {str(e)}')
            raise

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """流式聊天"""
        self.validate_request(request)

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
            log.error(f'slliconflow streaming error: {e.response.status_code}')
            raise Exception(f'slliconflow streaming error: {e.response.text}')
        except Exception as e:
            log.error(f'Unexpected streaming error: {str(e)}')
            raise

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
