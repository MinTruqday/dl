import httpx

from src.core.infrastructure.configuration import settings


async def collector_document_stats(source_ids: list[str]) -> dict:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.CONTENT_URL}/tai-lieu/noi-bo/thong-ke",
            json={"source_ids": source_ids},
            headers={"X-Internal-Token": settings.SECRET_KEY},
        )
    response.raise_for_status()
    return response.json()["data"]
