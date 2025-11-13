"""
@File    : model_registry.py.py
@Author  : Martin
@Time    : 2025/11/4 11:14
@Desc    :
"""

from app.adapters.base import BaseLLMAdapter, ModelProvider, ChatRequest
from app.adapters.ai_openai import OpenAIAdapter
from app.adapters.siliconflow import SiliconFlowAdapter
from app.adapters.deepseek import DeepSeekerAdapter
from app.core.config import settings
from app.main import log


class ModelRegistry:
    """
    模型注册中心
    管理所有可用的模型适配器
    """

    def __init__(self):
        self._adapters: dict[ModelProvider, type[BaseLLMAdapter]] = {}
        self._instances: dict[str, BaseLLMAdapter] = {}
        self._register_default_adapters()

    async def chat(self, request: ChatRequest):
        """根据 provider 调用对应适配器的 chat 方法"""
        adapter = self.get_adapter(provider=request.provider)
        if request.stream:
            # 如果是流式
            return adapter.chat_stream(request)
        else:
            # 非流式
            return await adapter.chat(request)

    def _register_default_adapters(self):
        """注册默认适配器"""
        self.register(ModelProvider.OPENAI, OpenAIAdapter)
        self.register(ModelProvider.SILICONFLOW, SiliconFlowAdapter)
        self.register(ModelProvider.DEEPSEEK, DeepSeekerAdapter)
        # 以后可以添加更多：
        # self.register(ModelProvider.CLAUDE, ClaudeAdapter)
        # self.register(ModelProvider.ZHIPU, ZhipuAdapter)

    def register(self, provider: ModelProvider, adapter_class: type[BaseLLMAdapter]):
        """注册适配器"""
        self._adapters[provider] = adapter_class
        log.info(f'Registered adapter: {provider}')

    def get_adapter(
            self, provider: ModelProvider, api_key: str | None = None, base_url: str | None = None
    ) -> BaseLLMAdapter:
        """
        获取适配器实例
        支持缓存，相同配置返回相同实例
        """
        # 创建缓存key
        cache_key = f'{provider}_{api_key}_{base_url}'

        # 检查缓存
        if cache_key in self._instances:
            return self._instances[cache_key]

        # 创建新实例
        if provider not in self._adapters:
            raise ValueError(f'Adapter for {provider} not registered')

        adapter_class = self._adapters[provider]

        # 如果没有提供api_key，从环境变量获取
        if not api_key:
            api_key = self._get_default_api_key(provider)

        instance = adapter_class(api_key=api_key, base_url=base_url)

        # 缓存实例
        self._instances[cache_key] = instance

        return instance

    def _get_default_api_key(self, provider: ModelProvider) -> str:
        """从配置获取默认API Key"""
        # 这里可以从环境变量或配置文件读取
        # 暂时返回空字符串，实际使用时需要配置
        key_map = {
            ModelProvider.OPENAI: getattr(settings, 'OPENAI_API_KEY', ''),
            ModelProvider.SILICONFLOW: getattr(settings, 'SILICONFLOW_API_KEY', ''),
            ModelProvider.DEEPSEEK: getattr(settings, 'DEEPSEEK_API_KEY', ''),
        }

        api_key = key_map.get(provider, '')
        # print('API key是：',api_key)
        if not api_key:
            raise ValueError(f'API key for {provider} not configured')

        return api_key

    def get_available_providers(self) -> list[ModelProvider]:
        """获取所有可用的供应商"""
        return list(self._adapters.keys())

    async def close_all(self):
        """关闭所有适配器实例"""
        for instance in self._instances.values():
            if hasattr(instance, 'close'):
                await instance.close()
        self._instances.clear()


# 全局注册中心实例
model_registry = ModelRegistry()
