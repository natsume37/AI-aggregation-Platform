# -*- coding: utf-8 -*-
"""
@File    : sflow-conect.py
@Author  : Martin
@Time    : 2025/11/4 14:44
@Desc    : 
"""
key = 'sk-olgljnebsvvenflnhjhkwlhorfocekffrwflxpinzogkiutx'
# run_siliconflow.py
import asyncio
from app.adapters.siliconflow import SiliconFlow
from app.adapters.base import ChatRequest, ChatMessage


async def main():
    # 1. 创建适配器（填你的真实 key）
    adapter = SiliconFlow(
        api_key=key,  # 改成你的真实 key
        base_url="https://api.siliconflow.cn/v1"
    )

    # 2. 构造请求
    request = ChatRequest(
        model="deepseek-ai/DeepSeek-V3",  # 推荐这个模型，稳定
        messages=[
            ChatMessage(role="user", content="你好，请用中文简单介绍 FastAPI")
        ],
        temperature=0.7,
        max_tokens=200,
        stream=False
    )

    # 3. 直接调用并打印结果
    response = await adapter.chat(request)
    print("回答:", response.content)

    # 4. 关闭
    await adapter.close()


# 运行
if __name__ == "__main__":
    asyncio.run(main())