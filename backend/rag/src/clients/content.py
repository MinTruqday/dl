import httpx
from fastapi.encoders import jsonable_encoder
from src.core.infrastructure.configuration import settings


class ContentClient:
    async def request(self, payload: dict):
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{settings.CONTENT_URL}/tai-lieu/noi-bo/tai-lieu",
                json=jsonable_encoder(payload),
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        response.raise_for_status()
        return response.json().get("data")

    async def get_document(self, document_id: str):
        document = await self.request(
            {"operation": "find_one", "query": {"_id": document_id}}
        )
        if document:
            return document
        return await self.request(
            {"operation": "find_one", "query": {"id": document_id}}
        )

    async def authorize_document(
        self,
        document_id: str,
        requester_id: str,
        is_admin: bool,
        allow_deleted: bool = False,
    ):
        document = await self.get_document(document_id)
        if not document or (document.get("is_deleted") is True and not allow_deleted):
            raise ValueError("Document not found")
        if not is_admin and str(document.get("creator_id")) != str(requester_id):
            raise PermissionError("Document access denied")
        return document

    async def authorize_read(
        self,
        document_id: str,
        requester_id: str,
        is_admin: bool,
    ):
        document = await self.get_document(document_id)
        if not document or document.get("is_deleted") is True:
            raise ValueError("Document not found")
        if (
            not is_admin
            and document.get("visibility") != "public"
            and str(document.get("creator_id")) != str(requester_id)
        ):
            raise PermissionError("Document access denied")
        return document

    async def mark_indexed(
        self,
        document_id: str,
        chunks_count: int,
        index_report: dict | None = None,
        extracted_text: str = "",
        extraction_method: str = "",
    ):
        return await self.request(
            {
                "operation": "update_one",
                "query": {"_id": document_id},
                "update": {
                    "$set": {
                        "chunks_count": chunks_count,
                        "is_indexed": True,
                        "indexing_status": "indexed",
                        "index_report": index_report or {"failed_chunks": [], "quarantined_chunks": []},
                        "extracted_text": extracted_text[:200000],
                        "extracted_text_truncated": len(extracted_text) > 200000,
                        "extraction_method": extraction_method,
                    },
                    "$unset": {"indexing_error": ""},
                },
            }
        )

    async def mark_indexing(self, document_id: str):
        return await self.request(
            {
                "operation": "update_one",
                "query": {"_id": document_id},
                "update": {"$set": {"indexing_status": "indexing"}, "$unset": {"indexing_error": ""}},
            }
        )

    async def mark_index_failed(self, document_id: str, error_code: str):
        return await self.request(
            {
                "operation": "update_one",
                "query": {"_id": document_id},
                "update": {"$set": {"indexing_status": "failed", "indexing_error": error_code}},
            }
        )

    async def mark_unindexed(self, document_id: str):
        return await self.request(
            {
                "operation": "update_one",
                "query": {"_id": document_id},
                "update": {"$set": {"chunks_count": 0, "is_indexed": False, "indexing_status": "not_started"}},
            }
        )


content_client = ContentClient()
