import httpx

from src.core.infrastructure.configuration import settings


class FinanceClient:
    @staticmethod
    async def get_purchase(user_id: str, document_id: str):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.FINANCE_URL}/tai-chinh/noi-bo/mua-hang",
                json={"action": "get_purchase", "user_id": user_id, "document_id": document_id},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data")
