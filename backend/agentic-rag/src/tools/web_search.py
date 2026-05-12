from tavily import TavilyClient
from src.core.config import settings
from loguru import logger

class WebSearchTool:
    def __init__(self):
        self.api_key = settings.TAVILY_API_KEY
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not found in settings. Web search will be disabled.")
            self.client = None
        else:
            self.client = TavilyClient(api_key=self.api_key)

    async def arun(self, query: str) -> str:
        if not self.client:
            return "Tính năng tìm kiếm Internet hiện đang tạm khóa (Thiếu API Key)."
        
        try:
            logger.info(f"Web search: Querying Tavily for '{query}'")
            response = self.client.search(query=query, search_depth="advanced", max_results=3)
            
            results = response.get("results", [])
            if not results:
                return "Không tìm thấy thông tin liên quan trên Internet."
            
            formatted_results = ""
            for i, res in enumerate(results, 1):
                title = res.get("title", "No Title")
                url = res.get("url", "#")
                content = res.get("content", "")
                formatted_results += f"[{i}] {title} ({url}): {content}\n\n"
            
            return formatted_results.strip()
        except Exception as e:
            logger.error(f"Tavily search error: {e}")
            return f"Gặp sự cố khi tìm kiếm Internet: {str(e)}"

web_search_tool = WebSearchTool()
