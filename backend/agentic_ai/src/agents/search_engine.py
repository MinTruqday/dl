import httpx
from core.config import settings
from loguru import logger

class SearchEngineAgent:
    async def execute(self, query: str) -> str:
        try:
            if not settings.TAVILY_API_KEY:
                logger.error("Lỗi hệ thống khi tìm kiếm dữ liệu cấu trúc")
                return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"
                
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    "[https://api.tavily.com/search](https://api.tavily.com/search)",
                    json={"api_key": settings.TAVILY_API_KEY, "query": query, "search_depth": "advanced", "include_answer": True},
                )
                if res.status_code == 200:
                    data = res.json()
                    logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
                    return data.get("answer", "\n".join([r.get("content", "") for r in data.get("results", [])]))
                return "Từ chối truy cập API nội bộ"
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

search_engine = SearchEngineAgent()