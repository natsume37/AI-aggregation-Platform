"""
@File    : news.py
@Author  : Martin
@Desc    : 新闻相关 Schema
"""

from pydantic import BaseModel, Field

class NewsResponse(BaseModel):
    """新闻接口响应"""
    image_url: str = Field(..., description="60秒读懂世界图片链接")
    date: str | None = Field(None, description="日期")

class NewsData(BaseModel):
    """新闻详细数据"""
    date: str = Field(..., description="日期")
    day_of_week: str = Field(..., description="星期")
    lunar_date: str = Field(..., description="农历日期")
    news: list[str] = Field(..., description="新闻列表")
    tip: str = Field(..., description="微语")
    image_url: str | None = Field(None, description="图片链接")

class NewsDetailResponse(BaseModel):
    """新闻详情响应"""
    news_data: NewsData = Field(..., description="新闻数据")

