import httpx

from src.core.infrastructure.configuration import settings


class ContentClient:
    @staticmethod
    async def exchange(action: str, **values):
        async with httpx.AsyncClient(timeout=10.0) as client:
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
    async def get(cls, document_id: str):
        return await cls.exchange("get_document", document_id=document_id)

    @classmethod
    async def get_accessible(cls, document_id: str, user_id: str, is_admin: bool, edit: bool = False):
        return await cls.exchange(
            "get_accessible_document",
            document_id=document_id,
            user_id=user_id,
            is_admin=is_admin,
            edit=edit,
        )

    @classmethod
    async def update_drm_policy(cls, document_id: str, values: dict):
        return await cls.exchange(
            "update_drm_policy",
            document_id=document_id,
            values=values,
        )
