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

    async def _tavily_image_search(self, query: str) -> list:
        response = await asyncio.to_thread(
            self.client.search, query=query, search_depth="advanced", max_results=4, include_images=True
        )
        images = response.get("images", [])
        import json
        formatted_images = []
        for img_url in images[:4]:
            formatted_images.append({
                "url": img_url,
                "width": 800,
                "height": 600
            })
        return json.dumps(formatted_images)

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
            except Exception as e:
                logger.exception("Primary search system encountered an issue")

        return "The system could not extract any valuable information from the search data sources"

    async def image_search(self, query: str) -> str:
        logger.info("Searching for images")

        if _is_ssrf_attempt(query):
            logger.warning("Blocked unauthorized network request")
            return "Request rejected due to severe violation of information security rules"

        if self.api_key_valid:
            try:
                result = await self._tavily_image_search(query)
                if result and result != "[]":
                    return result
            except Exception as e:
                logger.exception("Primary image search system encountered an issue")

        return "[]"

search_engine = EngineAgent()
