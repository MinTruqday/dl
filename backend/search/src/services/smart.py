from typing import List, Optional
import httpx
from loguru import logger
from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.configuration import settings
from src.services.document import DocumentService

class SmartService:

    @staticmethod
    @log_logic_execution
    async def smart_search(
        query: str,
        limit: int,
        authorization_header: Optional[str] = None,
    ) -> List[dict]:
        rag_url = settings.AGENTIC_AI_URL
        if not rag_url:
            return await DocumentService.search_documents(query, limit)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {}
                if authorization_header:
                    headers["Authorization"] = authorization_header
                resp = await client.post(
                    f"{rag_url}/suy-luan/tim-kiem-tai-lieu",
                    json={
                        "query": query,
                        "limit": min(limit, 30),
                    },
                    headers=headers,
                )
                if resp.status_code == 200:
                    payload = resp.json()
                    ranked = payload.get("results")
                    if isinstance(ranked, list):
                        documents = await DocumentService.get_ranked_public_documents(
                            ranked,
                            limit,
                        )
                        if documents:
                            return documents
                logger.warning("Semantic search returned no ranked public documents")
                return await DocumentService.search_documents(query, limit)
        except Exception:
            logger.exception("Semantic search execution error")
            return await DocumentService.search_documents(query, limit)
