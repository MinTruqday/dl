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
            logger.exception("Quá trình tìm kiếm bằng công cụ dự phòng đã thất bại")
            return ""

    async def execute(self, query: str) -> str:
        logger.info("Đang tìm kiếm thông tin")

        if _is_ssrf_attempt(query):
            logger.warning("Ngăn chặn yêu cầu mạng trái phép")
            return "Yêu cầu bị hệ thống từ chối do vi phạm nghiêm trọng các quy tắc bảo mật an toàn thông tin"

        if self.api_key_valid:
            try:
                result = await self._tavily_search(query)
                if result:
                    return result
                logger.warning("Đang chuyển sang công cụ tìm kiếm thay thế")
            except Exception as e:
                logger.exception("Hệ thống tra cứu chính gặp sự cố kết nối, tự động chuyển hướng sang cụm máy chủ dự phòng")

        result = await self._duckduckgo_search(query)
        if result:
            return result

        return "Hệ thống không thể trích xuất được bất kỳ thông tin nào có giá trị từ các nguồn dữ liệu tra cứu"

search_engine = EngineAgent()
