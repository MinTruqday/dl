from typing import Optional
from urllib.parse import quote

import httpx

from src.core.infrastructure.configuration import settings


class AccountClient:
    @staticmethod
    async def get_by_id(user_id: str) -> Optional[dict]:
        return await AccountClient._get(f"/xac-thuc/noi-bo/tai-khoan/{quote(user_id, safe='')}")

    @staticmethod
    async def get_by_email(email: str) -> Optional[dict]:
        return await AccountClient._get(f"/xac-thuc/noi-bo/tai-khoan/thu-dien-tu/{quote(email, safe='')}")

    @staticmethod
    async def _get(path: str) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.AUTHENTICATION_URL}{path}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json().get("data")
        except (httpx.HTTPError, ValueError):
            return None
