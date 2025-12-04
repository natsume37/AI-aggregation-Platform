"""
@File    : response.py
@Author  : Martin
@Desc    : 统一响应模型
"""

from typing import Generic, TypeVar, Any
from pydantic import BaseModel, Field

T = TypeVar("T")

class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""
    code: int = Field(default=200, description="业务状态码")
    message: str = Field(default="Success", description="响应消息")
    data: T | None = Field(default=None, description="响应数据")

    @classmethod
    def success(cls, data: T | None = None, message: str = "Success"):
        return cls(code=200, message=message, data=data)

    @classmethod
    def fail(cls, code: int = 400, message: str = "Failed", data: Any = None):
        return cls(code=code, message=message, data=data)
