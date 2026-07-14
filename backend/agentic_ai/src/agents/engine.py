import asyncio
import hashlib
import json
import re
from typing import List, Optional

import redis
from loguru import logger

from src.core.infrastructure.configuration import settings

def _is_ssrf_attempt(query: str) -> bool:
    import ipaddress
    import socket
    from urllib.parse import urlparse

    urls = re.findall(r"https?://[^\s]+", query)
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
    words = re.findall(r"[0-9a-fA-F.:]+", query)
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
    """
    <agent_role>
    <identity>Search Engine Agent</identity>
    <responsibility>Retrieves real-time external information using Tavily, with Redis caching and semantic re-ranking.</responsibility>
    <metis_behavior>Caches results for 30 minutes per query hash. Re-ranks results by semantic relevance before returning.</metis_behavior>
    </agent_role>
    """

    def __init__(self):
        self.api_key_valid = (
            settings.TAVILY_API_KEY is not None and len(settings.TAVILY_API_KEY) > 10
        )
        if self.api_key_valid:
            from tavily import TavilyClient
            self.client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        else:
            self.client = None

        self._redis: Optional[redis.Redis] = None
        try:
            self._redis = redis.from_url(settings.REDIS_URI, decode_responses=True)
            self._redis.ping()
        except Exception:
            logger.exception("Search engine Redis connection failed")
            self._redis = None

        self._reranker = None

    @property
    def reranker(self):
        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder
                self._reranker = CrossEncoder(settings.RERANKER_MODEL)
            except Exception:
                logger.exception("Search engine reranker loading failed")
                self._reranker = False
        return self._reranker

    def _cache_key(self, query: str) -> str:
        return f"search:{hashlib.sha256(query.encode()).hexdigest()}"

    def _load_cache(self, query: str) -> Optional[str]:
        if not self._redis:
            return None
        try:
            return self._redis.get(self._cache_key(query))
        except Exception:
            return None

    def _save_cache(self, query: str, result: str):
        if not self._redis:
            return
        try:
            self._redis.setex(self._cache_key(query), 1800, result)
        except Exception:
            logger.exception("Search cache write failed")

    def _rerank_results(self, query: str, results: List[dict]) -> List[dict]:
        current_reranker = self.reranker
        if not current_reranker or len(results) < 2:
            return results
        try:
            pairs = [[query, r.get("content", "")] for r in results]
            scores = current_reranker.predict(pairs)
            ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
            return [r for r, _ in ranked]
        except Exception:
            logger.exception("Search result re-ranking failed")
            return results

    async def _tavily_search(self, query: str) -> str:
        cached = self._load_cache(query)
        if cached:
            logger.info("Search cache hit")
            return cached

        response = await asyncio.to_thread(
            self.client.search, query=query, search_depth="advanced", max_results=8
        )
        results = response.get("results", [])
        if not results:
            return ""

        reranked = self._rerank_results(query, results)

        formatted = ""
        for res in reranked[:5]:
            formatted += f"- {res.get('title')} {res.get('content')}\n  Source link {res.get('url')}\n"

        self._save_cache(query, formatted)
        return formatted

    async def _tavily_image_search(self, query: str) -> list:
        response = await asyncio.to_thread(
            self.client.search, query=query, search_depth="advanced", max_results=4, include_images=True
        )
        images = response.get("images", [])
        formatted_images = [{"url": img_url, "width": 800, "height": 600} for img_url in images[:4]]
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
            except Exception:
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
            except Exception:
                logger.exception("Primary image search system encountered an issue")

        return "[]"


search_engine = EngineAgent()
