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


async def allowed_contacts(user_id: str, requested: list[str]) -> set[str]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{settings.MESSAGING_URL}/tin-nhan/noi-bo/lien-he-duoc-phep",
            json={"user_id": user_id, "requested": requested},
            headers={"X-Internal-Token": settings.SECRET_KEY},
        )
    response.raise_for_status()
    return set(response.json().get("allowed", []))
