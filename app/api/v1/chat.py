"""
@File    : chat.py
@Author  : Martin
@Time    : 2025/11/4 11:11
@Desc    :
"""

import json
from app.adapters.model_registry import model_registry
from app.api.deps import get_current_active_user
from app.core.database import get_db
from app.crud.conversation import conversation_crud
from app.main import log
from app.models.user import User
from app.schemas.chat import (
    AvailableModelsResponse,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationResponse,
    UsageInfo,
)
from app.services.chat_service import chat_service
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post('/completions', summary='聊天完成', response_model=ChatCompletionResponse)
async def create_chat_completion(
    request: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    创建聊天完成

    - **provider**: 模型供应商
    - **model**: 模型名称
    - **messages**: 消息列表
    - **temperature**: 温度参数
    - **conversation_id**: 对话ID（继续对话时提供）
    - **stream**: 是否流式响应 (此接口固定为 false)
    """
    if request.stream:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='此接口不支持流式响应，请使用流式专用接口')

    try:
        result = await chat_service.chat(
            db=db,
            user_id=current_user.id,
            provider=request.provider,
            model=request.model,
            messages=request.messages,
            conversation_id=request.conversation_id,
            save_conversation=request.save_conversation,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
        )

        # 构建响应
        return ChatCompletionResponse(
            id=result['id'],
            conversation_id=result['conversation_id'],
            model=result['model'],
            provider=result['provider'],
            content=result['content'],
            finish_reason=result['finish_reason'],
            usage=UsageInfo(**result['usage']),
            cost=result['cost'],
            response_time=result['response_time'],
            created_at=datetime.utcnow(),
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log.error(f'Chat completion error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to complete chat')


async def stream_chat_generator(request: ChatCompletionRequest, db: AsyncSession, current_user: User):
    """
    流式生成器，逐个返回流式数据块
    """
    try:
        # 调用 chat 方法，stream=True 会返回异步生成器
        generator = await chat_service.chat(
            db=db,
            user_id=current_user.id,
            provider=request.provider,
            model=request.model,
            messages=request.messages,
            conversation_id=request.conversation_id,
            save_conversation=request.save_conversation,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            top_p=request.top_p,
            frequency_penalty=request.frequency_penalty,
            presence_penalty=request.presence_penalty,
            stream=True,  # 启用流式模式
        )

        # 遍历异步生成器
        async for chunk in generator:
            # 每个 chunk 转换为 JSON 并以 SSE 格式发送
            yield f'data: {json.dumps(chunk)}\n\n'

    except ValueError as e:
        error_msg = {'error': str(e), 'type': 'validation_error'}
        yield f'data: {json.dumps(error_msg)}\n\n'
        log.error(f'Validation error in stream: {str(e)}')
    except Exception as e:
        error_msg = {'error': str(e), 'type': 'server_error'}
        yield f'data: {json.dumps(error_msg)}\n\n'
        log.error(f'Stream chat error: {str(e)}')


@router.post('/completions/stream', summary='流式聊天完成')
async def create_chat_stream_completion(
    request: ChatCompletionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    流式聊天完成 - 返回 Server-Sent Events (SSE) 格式的数据流

    客户端接收格式：
    ```
    data: {"content": "Hello", "finish_reason": null, ...}

    data: {"content": " world", "finish_reason": null, ...}

    data: {"content": "", "finish_reason": "stop", ...}
    ```
    """
    try:
        return StreamingResponse(
            stream_chat_generator(request, db, current_user),
            media_type='text/event-stream',
            headers={'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'X-Accel-Buffering': 'no'},
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        log.error(f'Stream setup error: {str(e)}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Failed to setup stream')


@router.get('/conversations', response_model=ConversationListResponse, summary='获取对话列表')
async def list_conversations(
    skip: int = Query(0, ge=0, description='跳过的记录数'),
    limit: int = Query(100, ge=1, le=100, description='返回的记录数'),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取当前用户的对话列表"""
    conversations = await conversation_crud.get_by_user(db, current_user.id, skip=skip, limit=limit)
    total = await conversation_crud.count_by_user(db, current_user.id)

    items = []
    for conv in conversations:
        messages = await conversation_crud.get_messages(db, conv.id)
        items.append(
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                model_name=conv.model_name,
                provider=conv.provider,
                message_count=len(messages),
                created_at=conv.created_at,
                updated_at=conv.updated_at,
            )
        )

    return ConversationListResponse(total=total, items=items)


@router.get('/conversations/{conversation_id}', response_model=ConversationDetailResponse, summary='获取对话详情')
async def get_conversation(
    conversation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """获取对话详情（包含所有消息）"""
    conversation = await conversation_crud.get_with_messages(db, conversation_id, current_user.id)

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found')

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        model_name=conversation.model_name,
        provider=conversation.provider,
        message_count=len(conversation.messages),
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=conversation.messages,
    )


@router.delete('/conversations/{conversation_id}', status_code=status.HTTP_204_NO_CONTENT, summary='删除对话')
async def delete_conversation(
    conversation_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """删除对话（会级联删除所有消息）"""
    conversation = await conversation_crud.get(db, conversation_id)

    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Conversation not found')

    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='Not enough privileges')

    await conversation_crud.delete(db, conversation_id)
    await db.commit()

    log.info(f'Conversation deleted: {conversation_id}')
    return None


@router.get('/models', response_model=list[AvailableModelsResponse], summary='获取可用模型列表')
async def list_available_models(current_user: User = Depends(get_current_active_user)):
    """获取所有可用的AI模型"""
    providers = model_registry.get_available_providers()

    result = []
    for provider in providers:
        try:
            adapter = model_registry.get_adapter(provider)
            models = await adapter.get_available_models()

            result.append(AvailableModelsResponse(provider=provider.value, models=models))
        except Exception as e:
            log.warning(f'Failed to get models for {provider}: {str(e)}')
            continue

    return result
