import httpx

from src.core.infrastructure.configuration import settings


class ContentClient:
    @staticmethod
    async def get(document_id: str):
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                f"{settings.CONTENT_URL}/tai-lieu/noi-bo/trao-doi",
                json={"action": "get_document", "document_id": document_id},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data")
