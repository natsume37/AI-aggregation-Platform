"""
@File    : chat.py.py
@Author  : Martin
@Time    : 2025/11/4 11:19
@Desc    :
"""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

# ========== 请求Schemas ==========


class ChatMessageRequest(BaseModel):
    """聊天消息请求"""

    role: str = Field(..., description='角色: system/user/assistant')
    content: str = Field(..., description='消息内容')


class ChatCompletionRequest(BaseModel):
    """聊天完成请求"""

    model: str = Field(..., description='模型名称')
    messages: list[ChatMessageRequest] = Field(..., description='消息列表')
    temperature: float = Field(default=0.7, ge=0, le=2, description='温度')
    max_tokens: int | None = Field(default=None, gt=0, description='最大token数')
    stream: bool = Field(default=False, description='是否流式响应')
    top_p: float = Field(default=1.0, ge=0, le=1, description='Top P')
    frequency_penalty: float = Field(default=0.0, ge=-2, le=2, description='频率惩罚')
    presence_penalty: float = Field(default=0.0, ge=-2, le=2, description='存在惩罚')

    # 对话相关
    conversation_id: int | None = Field(default=None, description='对话ID（继续对话时提供）')
    save_conversation: bool = Field(default=True, description='是否保存对话')


# ========== 响应Schemas ==========


class ChatMessageResponse(BaseModel):
    """消息响应"""

    id: int
    role: str
    content: str
    tokens: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 新增模型
class CompletionTokensDetails(BaseModel):
    reasoning_tokens: int | None = None
    model_config = ConfigDict(extra="ignore")


class UsageInfo(BaseModel):
    """使用信息"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

    # 添加新openAI规范
    completion_tokens_details: CompletionTokensDetails | None = None

    # 忽略未知字段避免报错
    model_config = ConfigDict(extra='ignore')


class ChatCompletionResponse(BaseModel):
    """聊天完成响应"""

    id: str = Field(..., description='响应ID')
    conversation_id: int = Field(..., description='对话ID')
    model: str = Field(..., description='使用的模型')
    provider: str = Field(..., description='模型供应商')
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
