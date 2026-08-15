import httpx
from typing import Dict, List, Optional
from src.core.infrastructure.configuration import settings

class RagClient:
    """Thin HTTP boundary to the standalone RAG service."""

    embedding_dimensions = 1024

    @staticmethod
    async def embed_query(text: str) -> List[float]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.RAG_URL}/rag/embedding/query",
                json={"text": text},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            embedding = data.get("embedding", [])
            if len(embedding) != RagClient.embedding_dimensions:
                raise RuntimeError("RAG embedding dimension mismatch")
            return embedding

    @staticmethod
    async def embed_batch(texts: List[str]) -> List[List[float]]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.RAG_URL}/rag/embedding/batch",
                json={"texts": texts},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            embeddings = data.get("embeddings", [])
            if len(embeddings) != len(texts) or any(
                len(embedding) != RagClient.embedding_dimensions
                for embedding in embeddings
            ):
                raise RuntimeError("RAG batch embedding dimension mismatch")
            return embeddings

    @staticmethod
    async def extract_attachment(data: str, filename: str = "attachment.pdf") -> str:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.RAG_URL}/rag/convert",
                json={"data": data, "filename": filename},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
            return str(response.json().get("data", {}).get("markdown") or "")

    @staticmethod
    async def retrieve(
        query: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        query_vector_override: Optional[List[float]] = None,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.RAG_URL}/rag/retrieve",
                json={
                    "query": query,
                    "document_ids": document_ids,
                    "k": k,
                    "query_vector_override": query_vector_override,
                    "requester_id": requester_id,
                    "is_admin": is_admin,
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            return data.get("documents", [])

    @staticmethod
    async def multi_query_retrieve(
        question: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(
                f"{settings.RAG_URL}/rag/multi-query-retrieve",
                json={
                    "question": question,
                    "document_ids": document_ids,
                    "k": k,
                    "requester_id": requester_id,
                    "is_admin": is_admin,
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            return data.get("documents", [])

    @staticmethod
    async def cross_document_retrieve(
        question: str,
        document_ids: List[str],
        k: int = 5,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.RAG_URL}/rag/cross-document-retrieve",
                json={
                    "question": question,
                    "document_ids": document_ids,
                    "k": k,
                    "requester_id": requester_id,
                    "is_admin": is_admin,
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
            response.raise_for_status()
            data = response.json().get("data", {})
            return data.get("documents", [])

    @staticmethod
    async def get_cache(
        query_text: str,
        query_vector: Optional[List[float]] = None,
    ) -> Optional[str]:
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

    @staticmethod
    async def set_cache(
        query_text: str,
        response_text: str,
        query_vector: Optional[List[float]] = None,
    ) -> None:
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

    @staticmethod
    async def ingest_document(
        document_id: str,
        requester_id: str,
        is_admin: bool = False,
        auth_token: Optional[str] = None,
    ) -> Dict:
        headers = {"X-Internal-Token": settings.SECRET_KEY}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.RAG_URL}/rag/ingest",
                json={
                    "document_id": document_id,
                    "requester_id": requester_id,
                    "is_admin": is_admin,
                },
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("data", {})

    @staticmethod
    async def extract_document(
        document_id: str,
        requester_id: str,
        is_admin: bool = False,
        auth_token: Optional[str] = None,
    ) -> str:
        headers = {"X-Internal-Token": settings.SECRET_KEY}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.RAG_URL}/rag/extract",
                json={
                    "document_id": document_id,
                    "requester_id": requester_id,
                    "is_admin": is_admin,
                },
                headers=headers,
            )
            response.raise_for_status()
            return str(response.json().get("data", {}).get("text") or "")

    @staticmethod
    async def delete_document(
        document_id: str,
        requester_id: str,
        is_admin: bool = False,
        auth_token: Optional[str] = None,
    ) -> Dict:
        headers = {"X-Internal-Token": settings.SECRET_KEY}
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.delete(
                f"{settings.RAG_URL}/rag/document/{document_id}",
                params={"requester_id": requester_id, "is_admin": is_admin},
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("data", {})

rag_client = RagClient()
