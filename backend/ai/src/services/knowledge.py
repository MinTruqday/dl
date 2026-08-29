from typing import Dict, List, Optional


class KnowledgeClient:
    embedding_dimensions = 1024

    @staticmethod
    async def embed_query(text: str) -> List[float]:
        from src.knowledge.services.embedding import embedder

        embedding = await embedder.embed_query(text)
        if len(embedding) != KnowledgeClient.embedding_dimensions:
            raise RuntimeError("Knowledge embedding dimension mismatch")
        return embedding

    @staticmethod
    async def embed_batch(texts: List[str]) -> List[List[float]]:
        from src.knowledge.services.embedding import embedder

        embeddings = await embedder.embed_batch(texts)
        if len(embeddings) != len(texts) or any(
            len(embedding) != KnowledgeClient.embedding_dimensions
            for embedding in embeddings
        ):
            raise RuntimeError("Knowledge batch embedding dimension mismatch")
        return embeddings

    @staticmethod
    async def extract_attachment(data: str, filename: str = "attachment.pdf") -> str:
        from src.knowledge.api.ingestion import convert_attachment
        from src.knowledge.schemas.ingestion import AttachmentConversionRequest

        result = await convert_attachment(
            AttachmentConversionRequest(data=data, filename=filename)
        )
        return str(result.data.get("markdown") or "")

    @staticmethod
    async def retrieve(
        query: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        query_vector_override: Optional[List[float]] = None,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        from src.knowledge.services.retrieval import retriever

        return await retriever.retrieve(
            query=query,
            document_ids=document_ids,
            k=k,
            query_vector_override=query_vector_override,
            requester_id=requester_id,
            is_admin=is_admin,
        )

    @staticmethod
    async def multi_query_retrieve(
        question: str,
        document_ids: Optional[List[str]] = None,
        k: int = 5,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        from src.knowledge.services.retrieval import retriever

        return await retriever.multi_query_retrieve(
            question=question,
            document_ids=document_ids,
            k=k,
            requester_id=requester_id,
            is_admin=is_admin,
        )

    @staticmethod
    async def cross_document_retrieve(
        question: str,
        document_ids: List[str],
        k: int = 5,
        requester_id: Optional[str] = None,
        is_admin: bool = False,
    ) -> List[Dict]:
        from src.knowledge.services.retrieval import retriever

        return await retriever.cross_document_retrieve(
            question=question,
            document_ids=document_ids,
            k=k,
            requester_id=requester_id,
            is_admin=is_admin,
        )

    @staticmethod
    async def get_cache(
        query_text: str, query_vector: Optional[List[float]] = None
    ) -> Optional[str]:
        from src.knowledge.services.cache import cache_service

        cached = await cache_service.get_response(query_text, query_vector)
        return cached.response if cached.hit else None

    @staticmethod
    async def set_cache(
        query_text: str,
        response_text: str,
        query_vector: Optional[List[float]] = None,
    ) -> None:
        from src.knowledge.services.cache import cache_service

        await cache_service.set_response(query_text, response_text, query_vector)

    @staticmethod
    async def ingest_document(
        document_id: str,
        requester_id: str,
        is_admin: bool = False,
        auth_token: Optional[str] = None,
    ) -> Dict:
        from src.knowledge.api.ingestion import ingest_document as ingest_operation
        from src.knowledge.schemas.ingestion import IngestRequest

        result = await ingest_operation(
            IngestRequest(
                document_id=document_id,
                requester_id=requester_id,
                is_admin=is_admin,
            ),
            None,
        )
        return result.data.model_dump()

    @staticmethod
    async def extract_document(
        document_id: str,
        requester_id: str,
        is_admin: bool = False,
        auth_token: Optional[str] = None,
    ) -> str:
        from src.knowledge.api.ingestion import extract_document as extract_operation
        from src.knowledge.schemas.ingestion import IngestRequest

        result = await extract_operation(
            IngestRequest(
                document_id=document_id,
                requester_id=requester_id,
                is_admin=is_admin,
            ),
            None,
        )
        return str(result.data.get("text") or "")

    @staticmethod
    async def delete_document(
        document_id: str,
        requester_id: str,
        is_admin: bool = False,
        auth_token: Optional[str] = None,
    ) -> Dict:
        from src.knowledge.api.ingestion import delete_document as delete_operation

        result = await delete_operation(
            document_id,
            requester_id=requester_id,
            is_admin=is_admin,
            user=None,
        )
        return result.data


knowledge_client = KnowledgeClient()
