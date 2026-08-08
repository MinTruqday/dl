import httpx

from src.core.infrastructure.configuration import settings


async def document_stats() -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.CONTENT_URL}/tai-lieu/noi-bo/thong-ke",
            json={},
            headers={"X-Internal-Token": settings.SECRET_KEY},
        )
    response.raise_for_status()
    return response.json()["data"]


async def analytics_documents(
    creator_id: str | None = None,
    search: str | None = None,
) -> list[dict]:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{settings.CONTENT_URL}/tai-lieu/noi-bo/trao-doi",
            json={
                "action": "list_analytics_documents",
                "creator_id": creator_id,
                "search": search,
            },
            headers={"X-Internal-Token": settings.SECRET_KEY},
        )
    response.raise_for_status()
    return response.json().get("data", [])
