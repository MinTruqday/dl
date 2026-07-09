import asyncio
import re

from loguru import logger

from src.core.infrastructure.configuration import settings

def _is_ssrf_attempt(query: str) -> bool:
    import socket
    import ipaddress
    from urllib.parse import urlparse
    urls = re.findall(r'https?://[^\s]+', query)
    for url in urls:
        try:
            hostname = urlparse(url).hostname
            if hostname:
                ip_info = socket.getaddrinfo(hostname, None)
                for res in ip_info:
                    ip = ipaddress.ip_address(res[4][0])
                    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified:
                        return True
        except Exception:
            pass
    words = re.findall(r'[0-9a-fA-F.:]+', query)
    for word in words:
        try:
            ip = ipaddress.ip_address(word.strip(".:"))
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified:
                return True
        except ValueError:
            pass
    if "localhost" in query.lower():
        try:
            ip_info = socket.getaddrinfo("localhost", None)
            for res in ip_info:
                ip = ipaddress.ip_address(res[4][0])
                if ip.is_private or ip.is_loopback:
                    return True
        except Exception:
            pass

    return False

class EngineAgent:
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
            formatted += f"- {res.get('title')} {res.get('content')}\n  Source link {res.get('url')}\n"
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
                formatted += f"- {res.get('title')} {res.get('body')}\n  Source link {res.get('href')}\n"
            return formatted
        except Exception as e:
            logger.exception("Search process using backup tool failed")
            return ""

    async def execute(self, query: str) -> str:
        logger.info("Searching for information")

        if _is_ssrf_attempt(query):
            logger.warning("Blocked unauthorized network request")
            return "Request rejected due to severe violation of information security rules"

        if self.api_key_valid:
            try:
                result = await self._tavily_search(query)
                if result:
                    return result
                logger.warning("Switching to alternative search tool")
            except Exception as e:
                logger.exception("Primary search system encountered a connection issue, automatically switching to backup servers")

        result = await self._duckduckgo_search(query)
        if result:
            return result

        return "The system could not extract any valuable information from the search data sources"

search_engine = EngineAgent()
