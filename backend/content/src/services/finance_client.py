import httpx

from src.core.infrastructure.configuration import settings


class FinanceClient:
    @staticmethod
    async def purchase(action: str, **values):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.FINANCE_URL}/tai-chinh/noi-bo/mua-hang",
                json={"action": action, **values},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        response.raise_for_status()
        return response.json().get("data")

    @classmethod
    async def has_purchase(cls, user_id: str, document_id: str) -> bool:
        result = await cls.purchase("has_purchase", user_id=user_id, document_id=document_id)
        return bool(result.get("purchased"))

    @classmethod
    async def purchase_count(cls, document_id: str) -> int:
        result = await cls.purchase("purchase_count", document_id=document_id)
        return int(result.get("count", 0))
