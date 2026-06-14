import asyncio
import re

from core.config import settings
from loguru import logger

_SSRF_PATTERN = re.compile(
    r"(localhost|127\.\d+\.\d+\.\d+|0\.0\.0\.0"
    r"|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+"
    r"|192\.168\.\d+\.\d+|169\.254\.\d+\.\d+"
    r"|::1|fd[0-9a-f]{2}:)",
    re.IGNORECASE,
)


def _is_ssrf_attempt(query: str) -> bool:
    return bool(_SSRF_PATTERN.search(query))


class SearchEngine:
    def __init__(self):
        self.api_key_valid = (
            settings.TAVILY_API_KEY is not None and len(settings.TAVILY_API_KEY) > 10
        )
        if self.api_key_valid:
            from tavily import TavilyClient

            self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        else:
            self.client = None

    async def _tavily_search(self, query: str) -> str:
        response = await asyncio.to_thread(
            self.client.search, query=query, search_depth="advanced", max_results=5
        )
        results = response.get("results", [])
        if not results:
            return ""
        formatted = ""
        for res in results:
            formatted += f"- {res.get('title')}: {res.get('content')}\n  (Source: {res.get('url')})\n"
        return formatted

    async def _duckduckgo_search(self, query: str) -> str:
        try:
            from duckduckgo_search import DDGS

            results = await asyncio.to_thread(
                lambda: list(DDGS().text(query, max_results=5))
            )
            if not results:
                return ""
            formatted = ""
            for res in results:
                formatted += f"- {res.get('title')}: {res.get('body')}\n  (Source: {res.get('href')})\n"
            return formatted
        except Exception as e:
            logger.error("Alternative web search failed due to error")
            return ""

    async def execute(self, query: str) -> str:
        logger.info("Searching for information for '{query}'")

        if _is_ssrf_attempt(query):
            logger.warning(f"Blocked SSRF attack attempt from query: {query}")
            return "This query is not allowed"

        if self.api_key_valid:
            try:
                result = await self._tavily_search(query)
                if result:
                    return result
                logger.warning(
                    "No results found from primary search engine, switching to alternative"
                )
            except Exception as e:
                logger.warning(
                    f"Primary web search failed: {e}. Automatically switching to alternative search engine"
                )

        result = await self._duckduckgo_search(query)
        if result:
            return result

        return "No relevant information found from available search sources"


search_engine = SearchEngine()
