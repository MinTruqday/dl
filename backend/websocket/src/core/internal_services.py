import httpx

from src.core.infrastructure.configuration import settings


async def document_exists(document_id: str, user_id: str = "", is_admin: bool = False, edit: bool = False) -> bool:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.CONTENT_URL}/tai-lieu/noi-bo/truy-cap",
            json={"document_id": document_id, "user_id": user_id, "is_admin": is_admin, "edit": edit},
            headers={"X-Internal-Token": settings.SECRET_KEY},
        )
    return response.status_code == 200
