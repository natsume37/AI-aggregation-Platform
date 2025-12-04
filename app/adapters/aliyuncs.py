"""
@File    : aliyuncs.py
@Author  : Martin
@Time    : 2025/11/14 20:00
"""

import httpx
from app.adapters.base import BaseLLMAdapter, ChatRequest, ChatResponse, ModelRequestError, StreamChunk
from app.core.config import settings
from app.core.enums import ModelProvider
import logging
from collections.abc import AsyncIterator

log = logging.getLogger("app")


class AliyunAsapter(BaseLLMAdapter):
    """阿里云服务适配器"""

    def __init__(self, api_key: str, base_url: str | None = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or 'https://dashscope.aliyuncs.com/compatible-mode/v1'
        self.provider = ModelProvider.ALIYUNCS

    async def _get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端"""
        return httpx.AsyncClient(
            base_url=self.base_url,
            headers={'Authorization': f'Bearer {self.api_key}', 'Content-Type': 'application/json'},
            timeout=settings.CONNECT_TIMEOUT,
        )

    def _build_payload(self, request: ChatRequest, is_stream: bool = False, is_enable_thinking: bool = False) -> dict:
        """构建请求 payload"""
        return {
            'model': request.model,
            'messages': [msg.model_dump(exclude_none=True) for msg in request.messages],
            'temperature': request.temperature,
            'max_tokens': request.max_tokens,
            'top_p': request.top_p,
            'frequency_penalty': request.frequency_penalty,
            'presence_penalty': request.presence_penalty,
            # 阿里非流式协议中需要显式关闭思考能力
            'enable_thinking': is_enable_thinking,
            'stream': is_stream,
        }

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """非流式聊天"""
        await self.validate_request(request)
        try:
            payload = self._build_payload(request, is_stream=False, is_enable_thinking=False)
            async with await self._get_client() as client:
                response = await client.post('/chat/completions', json=payload)
                response.raise_for_status()
                data = response.json()
            return ChatResponse(
                id=data['id'],
                model=data['model'],
                content=data['choices'][0]['message']['content'],
                finish_reason=data['choices'][0]['finish_reason'],
                usage={
                    'prompt_tokens': data['usage'].get('prompt_tokens', 0),
                    'completion_tokens': data['usage'].get('completion_tokens', 0),
                    'total_tokens': data['usage'].get('total_tokens', 0),
                },
                provider=self.provider,
            )
        except httpx.HTTPStatusError as e:
            log.error(f'aliyuncs API error: {e.response.status_code} - {e.response.text}')
            raise ModelRequestError(f'aliyuncs API error: {e.response.text}')

        except Exception as e:
            log.error(f'Unexpected aliyuncs error: {str(e)}')
            raise ModelRequestError(str(e))

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """流式聊天"""
        raise NotImplementedError("Aliyun stream not implemented")
        yield StreamChunk(content="", finish_reason="")

    async def get_available_models(self) -> list[str]:
        """获取可用模型列表（同步方法）"""
        return [
            'qwen-long',
            'qwq-plus',
            'qwq-plus-latest',
            'qwq-plus-2025-03-05',
            'qwen-max',
            'qwen-max-latest',
            'qwen-max-2025-01-25',
            'qwen-max-2024-09-19',
            'qwen-max-2024-04-28',
            'qwen-max-2024-04-03',
            'qwen-plus',
            'qwen-plus-latest',
            'qwen-plus-2025-04-28',
            'qwen-plus-2025-01-25',
            'qwen-plus-2025-01-12',
            'qwen-plus-2024-11-27',
            'qwen-plus-2024-11-25',
            'qwen-plus-2024-09-19',
            'qwen-plus-2024-08-06',
            'qwen-plus-2024-07-23',
            'qwen-turbo',
            'qwen-turbo-latest',
            'qwen-turbo-2025-04-28',
            'qwen-turbo-2025-02-11',
            'qwen-turbo-2024-11-01',
            'qwen-turbo-2024-09-19',
            'qwen-turbo-2024-06-24',
            'qwen-math-plus',
            'qwen-math-plus-latest',
            'qwen-math-plus-2024-09-19',
            'qwen-math-plus-2024-08-16',
            'qwen-math-turbo',
            'qwen-math-turbo-latest',
            'qwen-math-turbo-2024-09-19',
            'qwen-coder-plus',
            'qwen-coder-plus-latest',
            'qwen-coder-plus-2024-11-06',
            'qwen-coder-turbo',
            'qwen-coder-turbo-latest',
            'qwen-coder-turbo-2024-09-19',
            'qwq-32b',
            'qwq-32b-preview',
            'qwen3-235b-a22b',
            'qwen3-32b',
            'qwen3-30b-a3b',
            'qwen3-14b',
            'qwen3-8b',
            'qwen3-4b',
            'qwen3-1.7b',
            'qwen3-0.6b',
            'qwen2.5-14b-instruct-1m',
            'qwen2.5-7b-instruct-1m',
            'qwen2.5-72b-instruct',
            'qwen2.5-32b-instruct',
            'qwen2.5-14b-instruct',
            'qwen2.5-7b-instruct',
            'qwen2.5-3b-instruct',
            'qwen2.5-1.5b-instruct',
            'qwen2.5-0.5b-instruct',
            'qwen2.5-math-72b-instruct',
            'qwen2.5-math-7b-instruct',
            'qwen2.5-math-1.5b-instruct',
            'qwen2.5-coder-32b-instruct',
            'qwen2.5-coder-14b-instruct',
            'qwen2.5-coder-7b-instruct',
            'qwen2.5-coder-3b-instruct',
            'qwen2.5-coder-1.5b-instruct',
            'qwen2.5-coder-0.5b-instruct',
            'qwen2-57b-a14b-instruct',
            'qwen2-72b-instruct',
            'qwen2-7b-instruct',
            'qwen2-1.5b-instruct',
            'qwen2-0.5b-instruct',
            'qwen1.5-110b-chat',
            'qwen1.5-72b-chat',
            'qwen1.5-32b-chat',
            'qwen1.5-14b-chat',
            'qwen1.5-7b-chat',
            'qwen1.5-1.8b-chat',
            'qwen1.5-0.5b-chat',
            'codeqwen1.5-7b-chat',
        ]

    def calculate_cost(self, usage: dict[str, int], model: str) -> float:
        """计算成本"""
        return 0.0
