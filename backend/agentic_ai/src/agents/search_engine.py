import httpx
from core.config import settings
from loguru import logger

class SearchEngineAgent:
    async def execute(self, query: str) -> str:
        try:
            if not settings.TAVILY_API_KEY:
                logger.error("The external search indexing engine lacks vital required cryptographic system access configurations")
                return "The external informational search configuration is missing requiring administrative operational system intervention"
                
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(
                    "[https://api.tavily.com/search](https://api.tavily.com/search)",
                    json={"api_key": settings.TAVILY_API_KEY, "query": query, "search_depth": "advanced", "include_answer": True},
                )
                if res.status_code == 200:
                    data = res.json()
                    logger.info("The independent external search routing matrix fully finalized isolating optimal dynamic variables")
                    return data.get("answer", "\n".join([r.get("content", "") for r in data.get("results", [])]))
                return "The external search structural networking service forcibly rejected incoming analytical query parsing"
        except Exception:
            logger.error("The external distributed structural analytical mapping architecture brutally crashed disrupting informational search")
            return "The system encountered an unexpected error and requires you to try again later"

search_engine = SearchEngineAgent()