import httpx
from fastapi import HTTPException

from src.core.infrastructure.configuration import settings


class CollaborationClient:
    @staticmethod
    async def permission(document_id: str, user_id: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{settings.COLLABORATION_URL}/cong-tac/noi-bo/quyen",
                    json={"document_id": document_id, "user_id": user_id},
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
            response.raise_for_status()
            return response.json().get("data") or {}
        except httpx.HTTPError as error:
            raise HTTPException(
                status_code=503,
                detail="Dịch vụ cộng tác tạm thời không khả dụng",
            ) from error

    @classmethod
    async def can_edit(cls, document_id: str, user_id: str) -> bool:
        return bool((await cls.permission(document_id, user_id)).get("can_edit"))
