import httpx

from src.core.infrastructure.configuration import settings


class HumanityClient:
    @staticmethod
    async def request(method: str, path: str, **kwargs):
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method,
                f"{settings.HUMANITY_URL}{path}",
                headers={"X-Internal-Token": settings.SECRET_KEY},
                **kwargs,
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data")

    @classmethod
    async def get(cls, user_id: str):
        return await cls.request("GET", f"/nguoi-dung/{user_id}")

    @classmethod
    async def get_many(cls, user_ids: list[str]):
        return await cls.request("POST", "/nguoi-dung/hang-loat", json=user_ids)

    @classmethod
    async def find(cls, identifier: str):
        return await cls.request("POST", "/nguoi-dung/noi-bo/tim", json={"identifier": identifier})

    @classmethod
    async def list(cls, limit: int, offset: int):
        return await cls.request("GET", "/nguoi-dung/noi-bo/danh-sach", params={"limit": limit, "offset": offset})

    @classmethod
    async def update(cls, user_id: str, values: dict):
        await cls.request("PUT", f"/nguoi-dung/{user_id}", json=values)
        return True

    @classmethod
    async def stats(cls):
        return await cls.request("GET", "/nguoi-dung/noi-bo/thong-ke")
