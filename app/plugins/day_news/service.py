import datetime
import httpx
from fastapi import HTTPException, status


class NewsService:
    BASE_URL = "https://60s-static.viki.moe"
    # API_URL = "https://60s-static.viki.moe/60s/2025-12-01.json"

    # 定义请求头，模拟浏览器
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    async def get_news_image_url(self, date_str: str | None = None) -> str:
        """
        获取新闻图片URL
        """
        if not date_str:
            date_str = datetime.datetime.now().strftime('%Y-%m-%d')

        url = f"{self.BASE_URL}/images/{date_str}.png"

        # 验证链接有效性，同样加上 headers
        async with httpx.AsyncClient(headers=self.HEADERS, follow_redirects=True) as client:
            try:
                resp = await client.head(url)
                if resp.status_code != 200:
                    # 如果是今天，尝试昨天
                    if date_str == datetime.datetime.now().strftime('%Y-%m-%d'):
                        yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                        url = f"{self.BASE_URL}/images/{yesterday}.png"
                        resp = await client.head(url)
                        if resp.status_code != 200:
                            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                                detail="News not found for today or yesterday")
                    else:
                        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                            detail=f"News not found for date {date_str}")
            except httpx.RequestError as e:
                # 捕获网络连接错误
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Image connection failed: {str(e)}")

        return url

    async def get_news_image_bytes(self, date_str: str | None = None) -> bytes:
        """
        获取新闻图片二进制数据
        """
        url = await self.get_news_image_url(date_str)
        async with httpx.AsyncClient(headers=self.HEADERS, follow_redirects=True) as client:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Failed to download news image")
                return resp.content
            except httpx.RequestError as e:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Image download failed: {str(e)}")

    async def get_news_data(self) -> dict:
        """
        获取新闻JSON数据
        """
        today = datetime.datetime.now().strftime('%Y-%m-%d')
        api_url = f"https://60s-static.viki.moe/60s/{today}.json"

        # 关键修改：添加 headers 和 follow_redirects=True
        async with httpx.AsyncClient(headers=self.HEADERS, follow_redirects=True, timeout=10.0) as client:
            try:
                resp = await client.get(api_url)

                # 打印日志帮助调试（如果服务器有日志系统）
                # print(f"Status: {resp.status_code}, Content: {resp.text[:100]}")

                if resp.status_code != 200:
                     # 如果是今天，尝试昨天
                    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d')
                    api_url = f"https://60s-static.viki.moe/60s/{yesterday}.json"
                    resp = await client.get(api_url)

                resp.raise_for_status()  # 如果是 4xx 或 5xx 会抛出异常
                return resp.json()
            except httpx.HTTPStatusError as e:
                # 专门捕获 HTTP 状态错误（如 403, 404, 500）
                raise HTTPException(status_code=e.response.status_code, detail=f"API Error: {e.response.text}")
            except Exception as e:
                # 捕获其他错误（如连接超时、解析错误）
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                    detail=f"Failed to fetch news data: {str(e)}")


news_service = NewsService()

if __name__ == '__main__':
    import asyncio


    async def main():
        res = await news_service.get_news_data()
        print(res)


    asyncio.run(main())