import httpx

from src.core.infrastructure.configuration import settings


class EngagementClient:
    @staticmethod
    async def document_stats(document_id: str) -> dict:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.ENGAGEMENT_URL}/tuong-tac/noi-bo/thong-ke",
                json={"document_id": document_id},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        response.raise_for_status()
        return response.json().get("data") or {}
