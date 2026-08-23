import httpx

from src.core.infrastructure.configuration import settings


class AuthenticationClient:
    @classmethod
    async def get(cls, user_id: str):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.AUTHENTICATION_URL}/xac-thuc/noi-bo/tai-khoan/{user_id}",
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data")
