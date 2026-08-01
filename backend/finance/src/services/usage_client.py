import httpx

from src.core.infrastructure.configuration import settings


class UsageClient:
    @staticmethod
    async def request(method: str, user_id: str, **kwargs):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method,
                f"{settings.USAGE_URL}/goi-cuoc/{user_id}",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                **kwargs,
            )
        response.raise_for_status()
        return response.json().get("data")

    @classmethod
    async def get(cls, user_id: str):
        return await cls.request("GET", user_id)

    @classmethod
    async def update(cls, user_id: str, tier: str):
        return await cls.request("PUT", user_id, json={"ai_tier": tier, "is_premium": tier != "BASIC"})
