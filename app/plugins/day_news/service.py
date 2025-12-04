import datetime
import httpx
from fastapi import HTTPException, status

class NewsService:
    BASE_URL = "https://60s-static.viki.moe/images"
    API_URL = "https://60s.viki.moe/v2/60s?encoding=json"

    async def get_news_image_url(self, date_str: str | None = None) -> str:
        """
        获取新闻图片URL
        :param date_str: 日期字符串 (YYYY-MM-DD)，默认为今天
        :return: 图片URL
        """
        if not date_str:
            date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        
        url = f"{self.BASE_URL}/{date_str}.png"
        
        # 验证链接有效性
        async with httpx.AsyncClient() as client:
            resp = await client.head(url)
            if resp.status_code != 200:
                # 如果是今天，尝试昨天（可能今天还没更新）
                if date_str == datetime.datetime.now().strftime('%Y-%m-%d'):
                    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                    url = f"{self.BASE_URL}/{yesterday}.png"
                    resp = await client.head(url)
                    if resp.status_code != 200:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="News not found for today or yesterday")
                else:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"News not found for date {date_str}")
        
        return url

    async def get_news_image_bytes(self, date_str: str | None = None) -> bytes:
        """
        获取新闻图片二进制数据
        """
        url = await self.get_news_image_url(date_str)
        async with httpx.AsyncClient() as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to download news image")
            return resp.content

    async def get_news_data(self) -> dict:
        """
        获取新闻JSON数据
        """
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(self.API_URL)
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch news data: {str(e)}")

news_service = NewsService()
