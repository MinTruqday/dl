import httpx

from src.core.infrastructure.configuration import settings


class DrmClient:
    @staticmethod
    async def license_by_file(file_id: str):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.DRM_URL}/bao-ve/noi-bo/giay-phep",
                params={"file_id": file_id},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data")
