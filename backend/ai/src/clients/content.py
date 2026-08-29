import httpx

from src.core.infrastructure.configuration import settings


class ContentClient:
    @staticmethod
    async def exchange(action: str, **values):
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{settings.CONTENT_URL}/tai-lieu/noi-bo/trao-doi",
                json={"action": action, **values},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data")

    @classmethod
    async def accessible(cls, document_id: str, user_id: str, is_admin: bool):
        return await cls.exchange(
            "get_accessible_document",
            document_id=document_id,
            user_id=user_id,
            is_admin=is_admin,
            edit=True,
        )

    @classmethod
    async def authorize_document(
        cls, document_id: str, requester_id: str, is_admin: bool, allow_deleted: bool = False
    ):
        document = await cls.exchange(
            "get_accessible_document",
            document_id=document_id,
            user_id=requester_id,
            is_admin=is_admin,
            edit=True,
            allow_deleted=allow_deleted,
        )
        if not document:
            raise ValueError("Document not found")
        return document

    @classmethod
    async def authorize_read(cls, document_id: str, requester_id: str, is_admin: bool):
        document = await cls.exchange(
            "get_accessible_document",
            document_id=document_id,
            user_id=requester_id,
            is_admin=is_admin,
            edit=False,
        )
        if not document:
            raise ValueError("Document not found")
        return document

    @classmethod
    async def get(cls, document_id: str):
        return await cls.exchange("get_document", document_id=document_id)

    @classmethod
    async def update_index(
        cls,
        document_id: str,
        indexed_chunks: int,
        extraction_method: str,
        index_report: dict | None = None,
        extracted_text: str = "",
    ):
        return await cls.exchange(
            "update_index",
            document_id=document_id,
            indexed_chunks=indexed_chunks,
            extraction_method=extraction_method,
            index_report=index_report,
            extracted_text=extracted_text[:200000],
            extracted_text_truncated=len(extracted_text) > 200000,
        )

    @classmethod
    async def mark_indexed(
        cls,
        document_id: str,
        chunks_count: int,
        index_report: dict | None = None,
        extracted_text: str = "",
        extraction_method: str = "",
    ):
        return await cls.update_index(
            document_id,
            chunks_count,
            extraction_method,
            index_report,
            extracted_text,
        )

    @classmethod
    async def mark_indexing(cls, document_id: str):
        return await cls.exchange("mark_indexing", document_id=document_id)

    @classmethod
    async def mark_index_failed(cls, document_id: str, error_code: str):
        return await cls.exchange(
            "mark_index_failed", document_id=document_id, error_code=error_code
        )

    @classmethod
    async def mark_unindexed(cls, document_id: str):
        return await cls.exchange("mark_unindexed", document_id=document_id)

    @classmethod
    async def search(cls, query: str):
        return await cls.exchange("search_documents", query=query)
