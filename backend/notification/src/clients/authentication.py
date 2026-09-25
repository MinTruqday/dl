import httpx

from src.core.infrastructure.configuration import settings


class AuthenticationClient:
    @classmethod
    async def session_is_valid(cls, user_id: str, session_id: str) -> bool:
        try:
            async with httpx.AsyncClient(
                timeout=settings.INTERNAL_REQUEST_TIMEOUT_SECONDS
            ) as client:
                response = await client.get(
                    f"{settings.AUTHENTICATION_URL}/xac-thuc/noi-bo/phien/{session_id}/nguoi-dung/{user_id}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
            response.raise_for_status()
            return bool(response.json().get("data", {}).get("valid"))
        except (httpx.HTTPError, ValueError):
            return False

    @classmethod
    async def get(cls, user_id: str):
        async with httpx.AsyncClient(
            timeout=settings.INTERNAL_REQUEST_TIMEOUT_SECONDS
        ) as client:
            response = await client.get(
                f"{settings.AUTHENTICATION_URL}/xac-thuc/noi-bo/tai-khoan/{user_id}",
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data")
