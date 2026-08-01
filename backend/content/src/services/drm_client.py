import httpx

from src.core.infrastructure.configuration import settings


class DrmClient:
    @staticmethod
    async def request(path: str, **params):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{settings.DRM_URL}{path}",
                params=params,
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data")

    @classmethod
    async def license_by_file(cls, file_id: str):
        return await cls.request("/bao-ve/noi-bo/giay-phep", file_id=file_id)

    @classmethod
    async def document_settings(cls, document_id: str):
        return await cls.request("/bao-ve/noi-bo/cau-hinh", document_id=document_id)
