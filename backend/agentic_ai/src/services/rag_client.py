import httpx
from typing import Dict, List, Optional
from loguru import logger
from src.core.infrastructure.configuration import settings

class RagClient:
    @staticmethod
    async def embed_query(text: str) -> List[float]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.RAG_URL}/rag/embedding/query",
                    json={"text": text},
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                return data.get("embedding", [])
        except Exception:
            logger.exception("RagClient embed_query failed")
            return []

    @staticmethod
    async def embed_batch(texts: List[str]) -> List[List[float]]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.RAG_URL}/rag/embedding/batch",
                    json={"texts": texts},
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                return data.get("embeddings", [])
        except Exception:
            logger.exception("RagClient embed_batch failed")
            return []

    @staticmethod
    async def retrieve(
        query: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        query_vector_override: Optional[List[float]] = None,
    ) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.RAG_URL}/rag/retrieve",
                    json={
                        "query": query,
                        "document_ids": document_ids,
                        "k": k,
                        "query_vector_override": query_vector_override,
                    },
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                return data.get("documents", [])
        except Exception:
            logger.exception("RagClient retrieve failed")
            return []

    @staticmethod
    async def multi_query_retrieve(
        question: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
    ) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=45.0) as client:
                response = await client.post(
                    f"{settings.RAG_URL}/rag/multi-query-retrieve",
                    json={
                        "question": question,
                        "document_ids": document_ids,
                        "k": k,
                    },
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                return data.get("documents", [])
        except Exception:
            logger.exception("RagClient multi_query_retrieve failed")
            return []

    @staticmethod
    async def cross_document_retrieve(
        question: str,
        document_ids: List[str],
        k: int = 5,
    ) -> List[Dict]:
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.RAG_URL}/rag/cross-document-retrieve",
                    json={
                        "question": question,
                        "document_ids": document_ids,
                        "k": k,
                    },
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                return data.get("documents", [])
        except Exception:
            logger.exception("RagClient cross_document_retrieve failed")
            return []

    @staticmethod
    async def expand_graph(
        document_ids: List[str],
        seed_query: str,
        limit: int = 20,
    ) -> str:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{settings.RAG_URL}/rag/graph/expand",
                    json={
                        "document_ids": document_ids,
                        "seed_query": seed_query,
                        "limit": limit,
                    },
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                return data.get("context", "")
        except Exception:
            logger.exception("RagClient expand_graph failed")
            return ""

    @staticmethod
    async def get_cache(
        query_text: str,
        query_vector: Optional[List[float]] = None,
    ) -> Optional[str]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.RAG_URL}/rag/cache/get",
                    json={
                        "query_text": query_text,
                        "query_vector": query_vector,
                    },
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                response.raise_for_status()
                data = response.json().get("data", {})
                if data.get("hit"):
                    return data.get("response")
                return None
        except Exception:
            logger.exception("RagClient get_cache failed")
            return None

    @staticmethod
    async def set_cache(
        query_text: str,
        response_text: str,
        query_vector: Optional[List[float]] = None,
    ) -> None:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.RAG_URL}/rag/cache/set",
                    json={
                        "query_text": query_text,
                        "response_text": response_text,
                        "query_vector": query_vector,
                    },
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                response.raise_for_status()
        except Exception:
            logger.exception("RagClient set_cache failed")

    @staticmethod
    async def ingest_document(document_id: str, auth_token: Optional[str] = None) -> Dict:
        headers = {"X-Internal-Token": settings.SECRET_KEY}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.RAG_URL}/rag/ingest",
                json={"document_id": document_id},
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("data", {})

rag_client = RagClient()
