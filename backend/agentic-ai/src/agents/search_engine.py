import asyncio
from loguru import logger
from tavily import TavilyClient
from src.core.config import settings

class SearchEngine:
    def __init__(self):
        self.api_key_valid = settings.TAVILY_API_KEY is not None and len(settings.TAVILY_API_KEY) > 10
        if self.api_key_valid:
            self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        else:
            self.client = None

    async def execute(self, query: str) -> str:
        logger.info(f"SearchEngine: Querying Tavily for '{query}'")
        
        if not self.api_key_valid:
            logger.warning("SearchEngine: TAVILY_API_KEY not found or invalid, skipping web search")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

        try:
            response = await asyncio.to_thread(
                self.client.search,
                query=query,
                search_depth="advanced",
                max_results=3
            )
            results = response.get("results", [])
            
            if not results:
                return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."
                
            formatted_result = ""
            for res in results:
                formatted_result += f"- {res.get('title')}: {res.get('content')}\n  (Source: {res.get('url')})\n"
                
            return formatted_result
        except Exception as e:
            logger.error(f"SearchEngine: Tavily search failed: {e}")
            return "Hệ thống đang gặp sự cố, vui lòng thử lại sau."

search_engine = SearchEngine()
