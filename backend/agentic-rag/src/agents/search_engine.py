import os
from loguru import logger
from tavily import AsyncTavilyClient

tavily_api_key = os.environ.get("TAVILY_API_KEY", "tvly-mock-key")

class SearchEngineAgent:
    def __init__(self):
        self.api_key_valid = tavily_api_key != "tvly-mock-key" and len(tavily_api_key) > 10
        if self.api_key_valid:
            self.client = AsyncTavilyClient(api_key=tavily_api_key)
        else:
            self.client = None

    async def execute(self, query: str) -> str:
        logger.info(f"SearchEngine: Tìm kiếm với query: {query}")
        
        if not self.api_key_valid:
            logger.warning("SearchEngine: Không tìm thấy TAVILY_API_KEY hợp lệ. Bỏ qua tìm kiếm thực tế.")
            return f"Kết quả tìm kiếm cho '{query}': Không có dữ liệu do thiếu cấu hình API Key. Hãy thử tìm trong cơ sở dữ liệu nội bộ."

        try:
            response = await self.client.search(query=query, search_depth="advanced", max_results=3)
            results = response.get("results", [])
            
            if not results:
                return f"Không tìm thấy kết quả nào trên mạng cho: {query}"
                
            formatted_result = "Dữ liệu tìm được trên Internet:\n"
            for res in results:
                formatted_result += f"- {res.get('title')}: {res.get('content')}\n  (Nguồn: {res.get('url')})\n"
                
            return formatted_result
        except Exception as e:
            logger.error(f"SearchEngine: Lỗi tìm kiếm Tavily: {e}")
            return "Hệ thống gặp sự cố khi truy cập dữ liệu Internet."

search_engine_agent = SearchEngineAgent()
