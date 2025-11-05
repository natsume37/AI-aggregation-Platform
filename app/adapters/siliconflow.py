# -*- coding: utf-8 -*-
"""
@File    : silicon_flow.py
@Author  : Martin
@Time    : 2025/11/4 11:10
@Desc    :
"""

from typing import AsyncIterator, List, Dict, Optional
import httpx
import json
from app.adapters.base import (
    BaseLLMAdapter,
    ChatRequest,
    ChatResponse,
    StreamChunk,
    ModelProvider,
    ChatMessage,
)
from app.core.logging import log


class SiliconFlow(BaseLLMAdapter):
    """OpenAI API适配器"""

    # 模型定价 (USD per 1K tokens)
    MODEL_PRICING = {
        "deepseek-ai/DeepSeek-V3": {"prompt": 0.03, "completion": 0.06},
        "deepseek-ai/DeepSeek-V3.1": {"prompt": 0.01, "completion": 0.03},
        "inclusionAI/Ling-flash-2.0": {"prompt": 0.0005, "completion": 0.0015},
        "stepfun-ai/step3": {"prompt": 0.003, "completion": 0.004},
    }

    def __init__(self, api_key: str, base_url: Optional[str] = None):
        super().__init__(api_key, base_url)
        self.base_url = base_url or "https://api.siliconflow.cn/v1"
        self.provider = ModelProvider.SILICONFLOW
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=60.0,
        )

    def get_model_pricing(self):
        url = "https://api.siliconflow.cn/v1/models"
        headers = {"Authorization": "Bearer <token>"}

        response = httpx.get(url, headers=headers)
        print(response.json())

    def get_available_models(self) -> List[str]:
        """获取可用模型列表"""
        return list(self.MODEL_PRICING.keys())

    def calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """计算成本"""
        if model not in self.MODEL_PRICING:
            return 0.0

        pricing = self.MODEL_PRICING[model]
        prompt_cost = (usage.get("prompt_tokens", 0) / 1000) * pricing["prompt"]
        completion_cost = (usage.get("completion_tokens", 0) / 1000) * pricing[
            "completion"
        ]

        return prompt_cost + completion_cost

    async def chat(self, request: ChatRequest) -> ChatResponse:
        """非流式聊天"""
        self.validate_request(request)

        # 构建请求体
        payload = {
            "model": request.model,
            "messages": [msg.model_dump(exclude_none=True) for msg in request.messages],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": False,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        try:
            response = await self.client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            # 解析响应
            choice = data["choices"][0]
            message = choice["message"]

            return ChatResponse(
                id=data["id"],
                model=data["model"],
                content=message["content"],
                finish_reason=choice["finish_reason"],
                usage=data["usage"],
                provider=self.provider,
            )

        except httpx.HTTPStatusError as e:
            log.error(
                f"slliconflow API error: {e.response.status_code} - {e.response.text}"
            )
            raise Exception(f"slliconflow API error: {e.response.text}")
        except Exception as e:
            log.error(f"Unexpected error: {str(e)}")
            raise

    async def chat_stream(self, request: ChatRequest) -> AsyncIterator[StreamChunk]:
        """流式聊天"""
        self.validate_request(request)

        # 构建请求体
        payload = {
            "model": request.model,
            "messages": [msg.model_dump(exclude_none=True) for msg in request.messages],
            "temperature": request.temperature,
            "top_p": request.top_p,
            "frequency_penalty": request.frequency_penalty,
            "presence_penalty": request.presence_penalty,
            "stream": True,
        }

        if request.max_tokens:
            payload["max_tokens"] = request.max_tokens

        try:
            async with self.client.stream(
                "POST", "/chat/completions", json=payload
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line.strip():
                        continue

                    if line.startswith("data: "):
                        data_str = line[6:]

                        if data_str == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            choice = data["choices"][0]
                            delta = choice.get("delta", {})

                            if "content" in delta:
                                yield StreamChunk(
                                    content=delta["content"], finish_reason=None
                                )

                            if choice.get("finish_reason"):
                                yield StreamChunk(
                                    content="", finish_reason=choice["finish_reason"]
                                )

                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            log.error(f"slliconflow streaming error: {e.response.status_code}")
            raise Exception(f"slliconflow streaming error: {e.response.text}")
        except Exception as e:
            log.error(f"Unexpected streaming error: {str(e)}")
            raise

    async def close(self):
        """关闭客户端"""
        await self.client.aclose()
