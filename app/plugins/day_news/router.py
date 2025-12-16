# -*- coding: utf-8 -*-
"""
@File    : router.py
@Author  : Martin
@Time    : 2025/12/4 11:12
@Desc    : everyday day_news router
"""
from fastapi import APIRouter, Query
from fastapi.responses import Response
from app.plugins.day_news.service import news_service
from app.schemas.response import ResponseModel
from app.schemas.news import NewsResponse, NewsDetailResponse, NewsData

router = APIRouter(prefix="/tools/news", tags=["Tools"])

@router.get("/image", summary="获取每日新闻图片(流)")
async def get_news_image(date: str | None = Query(None, description="日期 (YYYY-MM-DD)，默认今天")):
    """
    获取每日新闻图片（直接返回图片流）
    """
    image_content = await news_service.get_news_image_bytes(date)
    return Response(content=image_content, media_type="image/png")

@router.get("/", summary="获取每日新闻图片URL", response_model=ResponseModel[NewsResponse])
async def get_news_url(date: str | None = Query(None, description="日期 (YYYY-MM-DD)，默认今天")):
    """
    获取每日新闻图片URL
    """
    url = await news_service.get_news_image_url(date)
    return ResponseModel.success(data=NewsResponse(image_url=url, date=date or "today"))

@router.get("/json", summary="获取每日新闻完整JSON数据", response_model=ResponseModel[NewsDetailResponse])
async def get_news_json():
    """
    获取每日新闻完整结构化数据
    """
    result = await news_service.get_news_data()
    if result.get("code") != 200:
        return ResponseModel.fail(message=f"获取失败: {result.get('message')}")
    
    data = result.get("data", {})
    # 补充图片链接
    image_url = await news_service.get_news_image_url()
    
    news_data = NewsData(
        date=data.get("date", ""),
        day_of_week=data.get("day_of_week", ""),
        lunar_date=data.get("lunar_date", ""),
        news=data.get("news", []),
        tip=data.get("tip", ""),
        image_url=image_url
    )
    
    return ResponseModel.success(data=NewsDetailResponse(news_data=news_data))

@router.get("/text", summary="获取每日新闻文本")
async def get_news_text():
    """
    获取每日新闻纯文本
    """
    try:
        result = await news_service.get_news_data()
        if result.get("code") != 200:
            return Response(content=f"获取失败: {result.get('message')}", media_type="text/plain")
        
        data = result.get("data", {})
        news_list = data.get("news", [])
        
        # 构建文本
        lines = []
        header = f"{data.get('date')} {data.get('day_of_week')} {data.get('lunar_date')}"
        lines.append(header)
        lines.append("-" * 30)
        
        for idx, news in enumerate(news_list, 1):
            lines.append(f"{idx}. {news}")
            
        if data.get("tip"):
            lines.append("")
            lines.append(f"【微语】{data.get('tip')}")
            
        return Response(content="\n".join(lines), media_type="text/plain")
    except Exception as e:
        return Response(content=f"Error: {str(e)}", media_type="text/plain")



