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
    async def get(cls, document_id: str):
        return await cls.exchange("get_document", document_id=document_id)

    @classmethod
    async def update_index(cls, document_id: str, indexed_chunks: int, extraction_method: str):
        return await cls.exchange(
            "update_index",
            document_id=document_id,
            indexed_chunks=indexed_chunks,
            extraction_method=extraction_method,
        )

    @classmethod
    async def search(cls, query: str):
        return await cls.exchange("search_documents", query=query)
