"""
@File    : enums.py
@Author  : Martin
@Time    : 2025/11/13
@Desc    : 全局枚举定义
"""

from enum import Enum


class ModelProvider(str, Enum):
    """模型供应商枚举"""

    OPENAI = 'openai'
    DEEPSEEK = 'deepseek'
    SILICONFLOW = 'siliconflow'
    ALIYUNCS = 'aliyuncs'
    # 可以继续添加...
    # CLAUDE = 'claude'
    # QWEN = 'qwen'
