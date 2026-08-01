from typing import Optional
from urllib.parse import quote

import httpx

from src.core.infrastructure.configuration import settings


class UserDirectory:
    @staticmethod
    async def get_by_id(user_id: str) -> Optional[dict]:
        return await UserDirectory._get(f"/nguoi-dung/{quote(user_id, safe='')}")

    @staticmethod
    async def get_by_email(email: str) -> Optional[dict]:
        return await UserDirectory._get(f"/nguoi-dung/email/{quote(email, safe='')}")

    @staticmethod
    async def _get(path: str) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.HUMANITY_URL}{path}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json().get("data")
        except (httpx.HTTPError, ValueError):
            return None
