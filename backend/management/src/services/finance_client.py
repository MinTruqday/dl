import httpx

from src.core.infrastructure.configuration import settings


async def author_analytics(
    user_id: str,
    document_ids: list[str],
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{settings.FINANCE_URL}/tai-chinh/noi-bo/mua-hang",
            json={
                "action": "author_analytics",
                "user_id": user_id,
                "document_ids": document_ids,
                "from_date": from_date,
                "to_date": to_date,
            },
            headers={"X-Internal-Token": settings.SECRET_KEY},
        )
    response.raise_for_status()
    return response.json().get("data", {})


async def system_analytics(
    from_date: str | None = None,
    to_date: str | None = None,
) -> dict:
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            f"{settings.FINANCE_URL}/tai-chinh/noi-bo/mua-hang",
            json={
                "action": "system_analytics",
                "from_date": from_date,
                "to_date": to_date,
            },
            headers={"X-Internal-Token": settings.SECRET_KEY},
        )
    response.raise_for_status()
    return response.json().get("data", {})
