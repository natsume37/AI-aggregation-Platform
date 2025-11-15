"""
@File    : chat.py
@Author  : Martin
@Time    : 2025/11/4 11:19
@Desc    : 聊天相关的 Pydantic Schemas（API 层）
"""

# ✅ 从 core.enums 导入
from app.core.enums import ModelProvider
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ==================== 请求 Schemas（API 层使用）====================


class ChatMessageRequest(BaseModel):
    """聊天消息请求（API 层）"""

    role: str = Field(..., description='角色: system/user/assistant')
    content: str = Field(..., description='消息内容')


class ChatCompletionRequest(BaseModel):
    """聊天完成请求（API 层）"""

    provider: ModelProvider = Field(..., description='模型供应商')  # ← 枚举类型
    model: str = Field(..., description='模型名称')
    messages: list[ChatMessageRequest] = Field(..., description='消息列表')  # ← ChatMessageRequest
    temperature: float = Field(default=0.7, ge=0, le=2, description='温度')
    max_tokens: int | None = Field(default=None, gt=0, description='最大token数')
    stream: bool = Field(default=False, description='是否流式响应')
    top_p: float = Field(default=1.0, ge=0, le=1, description='Top P')
    frequency_penalty: float = Field(default=0.0, ge=-2, le=2, description='频率惩罚')
    presence_penalty: float = Field(default=0.0, ge=-2, le=2, description='存在惩罚')

    # 对话相关
    conversation_id: int | None = Field(default=None, description='对话ID')
    save_conversation: bool = Field(default=True, description='是否保存对话')

    @field_validator('provider', mode='before')
    @classmethod
    def validate_provider(cls, v):
        """支持字符串输入，自动转换为枚举"""
        if isinstance(v, str):
            try:
                return ModelProvider(v.lower())
            except ValueError:
                available = [p.value for p in ModelProvider]
                raise ValueError(f"Invalid provider '{v}'. Available: {available}")
        return v


# ==================== 响应 Schemas ====================


class ChatMessageResponse(BaseModel):
    """消息响应"""

    id: int
    role: str
    content: str
    tokens: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CompletionTokensDetails(BaseModel):
    """Token详情（OpenAI 新增）"""

    reasoning_tokens: int | None = None
    model_config = ConfigDict(extra='ignore')


class UsageInfo(BaseModel):
    """使用信息"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    # OpenAI 新增字段
    completion_tokens_details: CompletionTokensDetails | None = None

    # 忽略未知字段
    model_config = ConfigDict(extra='ignore')


class ChatCompletionResponse(BaseModel):
    """聊天完成响应"""

    id: str = Field(..., description='响应ID')
    conversation_id: int = Field(..., description='对话ID')
    model: str = Field(..., description='使用的模型')
    provider: str = Field(..., description='模型供应商')  # ← 响应时用字符串
    content: str = Field(..., description='回复内容')
    finish_reason: str = Field(..., description='结束原因')
    usage: UsageInfo = Field(..., description='Token使用情况')
    cost: float = Field(..., description='成本(USD)')
    response_time: float = Field(..., description='响应时间(秒)')
    created_at: datetime = Field(..., description='创建时间')


class ConversationResponse(BaseModel):
    """对话响应"""

    id: int
    title: str
    model_name: str
    provider: str
    message_count: int = 0
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(ConversationResponse):
    """对话详情响应"""

    messages: list[ChatMessageResponse]


class ConversationListResponse(BaseModel):
    """对话列表响应"""

    total: int
    items: list[ConversationResponse]


class AvailableModelsResponse(BaseModel):
    """可用模型响应"""

    provider: str
    models: list[str]
