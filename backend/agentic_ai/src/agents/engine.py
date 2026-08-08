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
            parsed = urlparse(url)
            hostname = parsed.hostname
            if parsed.username or parsed.password or not hostname:
                return True
            if hostname:
                ip_info = socket.getaddrinfo(hostname, None)
                for res in ip_info:
                    ip = ipaddress.ip_address(res[4][0])
                    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_unspecified:
                        return True
        except Exception:
            return True
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
            return True
    return False

class EngineAgent:
    """
    <module_purpose>
    DocLib Engine Agent for real-time external information retrieval with caching and semantic re-ranking.
    </module_purpose>
    <contract>
    - Precondition: Tavily API key and Redis connection configured.
    - Postcondition: Returns re-ranked search results as formatted strings.
    - Error Handling: Returns safe fallback strings if dependencies fail. Does not crash.
    </contract>
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

    async def _tavily_search(self, query: str) -> List[dict]:
        cached = self._load_cache(query)
        if cached:
            logger.info("Search cache hit")
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                pass

        response = await asyncio.to_thread(
            self.client.search, query=query, search_depth="advanced", max_results=8
        )
        results = response.get("results", [])
        if not results:
            return []

        reranked = self._rerank_results(query, results)
        normalized = [
            {
                "title": result.get("title", ""),
                "content": result.get("content", ""),
                "url": result.get("url", ""),
            }
            for result in reranked[:5]
        ]
        self._save_cache(query, json.dumps(normalized, ensure_ascii=False))
        return normalized

    async def _playwright_scrape(self, url: str) -> str:
        if _is_ssrf_attempt(url):
            logger.warning("Playwright navigation blocked by SSRF policy")
            return ""
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, timeout=10000)
                content = await page.evaluate("() => document.body.innerText")
                await browser.close()
                return content[:5000]
        except ImportError:
            logger.warning("Playwright not installed. Fallback failed")
            return ""
        except Exception:
            logger.exception("Playwright scrape failed")
            return ""

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
            return json.dumps({"status": "network_request_blocked"})

        if not self.api_key_valid:
            return json.dumps({"status": "search_service_unavailable"})

        try:
            from langchain_core.messages import HumanMessage
            from src.utils.huggingface import create_chat_model
            from src.schemas.engine import SearchEvaluation, SubQueries
            from src.core.registry import registry, PromptType
            
            llm = create_chat_model()
            structured_llm = llm.with_structured_output(SubQueries)
            evaluation_llm = llm.with_structured_output(SearchEvaluation)
            
            max_iterations = 3
            accumulated_results = []
            current_query = query
            
            for i in range(max_iterations):
                prompt = registry.get(PromptType.ENGINE_SUBQUERIES).format(query=current_query)
                response = await structured_llm.ainvoke([HumanMessage(content=prompt)])
                
                search_queries = response.queries if response.queries else [current_query]
                if current_query not in search_queries:
                    search_queries.append(current_query)
                    
                search_queries = search_queries[:3]
                logger.info(f"Agentic RAG Iteration {i+1} - Sub-queries: {search_queries}")
                
                tasks = [self._tavily_search(q) for q in search_queries]
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for result in results:
                    if isinstance(result, list):
                        accumulated_results.extend(result)
                
                if not accumulated_results:
                    break

                eval_prompt_template = registry.get(PromptType.AGENTIC_SEARCH_EVALUATION)
                eval_prompt = eval_prompt_template.format(
                    query=query,
                    information=json.dumps(
                        accumulated_results,
                        ensure_ascii=False,
                    )[:5000],
                )
                eval_response = await evaluation_llm.ainvoke(
                    [HumanMessage(content=eval_prompt)]
                )
                
                if eval_response.sufficient:
                    logger.info("Self-evaluation: Sufficient information gathered")
                    break
                else:
                    logger.info("Self-evaluation: Insufficient information. Re-formulating query")
                    
                    urls = [
                        result.get("url")
                        for result in accumulated_results
                        if result.get("url")
                    ]
                    if urls:
                        logger.info(f"Triggering Playwright fallback on {urls[0]}")
                        scraped = await self._playwright_scrape(urls[0])
                        if scraped:
                            accumulated_results.append(
                                {
                                    "title": "",
                                    "content": scraped,
                                    "url": urls[0],
                                }
                            )
                    candidates = [
                        candidate
                        for candidate in search_queries
                        if candidate != current_query
                    ]
                    current_query = candidates[-1] if candidates else query
                    
            if accumulated_results:
                return json.dumps(
                    {"status": "success", "results": accumulated_results},
                    ensure_ascii=False,
                )
                
        except Exception:
            logger.exception("Agentic RAG search system encountered an issue")

        return json.dumps({"status": "search_results_unavailable"})

    async def image_search(self, query: str) -> str:
        logger.info("Searching for images")

        if _is_ssrf_attempt(query):
            logger.warning("Blocked unauthorized network request")
            return json.dumps({"status": "network_request_blocked"})

        if self.api_key_valid:
            try:
                result = await self._tavily_image_search(query)
                if result and result != "[]":
                    return result
            except Exception:
                logger.exception("Primary image search system encountered an issue")

        return "[]"


search_engine = EngineAgent()
