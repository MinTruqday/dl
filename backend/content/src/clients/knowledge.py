import httpx
from fastapi import HTTPException

from src.core.infrastructure.configuration import settings


class RagClient:
    async def delete_document(self, document_id: str, requester_id: str, is_admin: bool = False):
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.delete(
                    f"{settings.RAG_URL}/rag/document/{document_id}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                    params={"requester_id": requester_id, "is_admin": str(is_admin).lower()},
                )
        except httpx.HTTPError as error:
            raise HTTPException(status_code=503, detail="Không thể xóa chỉ mục tài liệu") from error
        if response.status_code >= 400:
            raise HTTPException(status_code=503, detail="Không thể xóa chỉ mục tài liệu")
        return response.json()


rag_client = RagClient()
