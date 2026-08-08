import httpx
from fastapi.encoders import jsonable_encoder
from src.core.infrastructure.configuration import settings


class DocumentCursor:
    def __init__(self, query: dict, projection: dict = None):
        self.query = query
        self.projection = projection
        self.sort_fields = []
        self.result_limit = 100

    def sort(self, field, direction=None):
        if direction is None and isinstance(field, list):
            self.sort_fields = field
        else:
            self.sort_fields = [(field, direction)]
        return self

    def limit(self, value: int):
        self.result_limit = value
        return self

    async def to_list(self, length=None):
        limit = self.result_limit if length is None else min(self.result_limit, length)
        return await DocumentRepository.request(
            {
                "operation": "find_many",
                "query": self.query,
                "projection": self.projection,
                "sort": self.sort_fields,
                "limit": limit,
            }
        )

class DocumentRepository:
    @classmethod
    async def request(cls, payload: dict):
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.CONTENT_URL}/tai-lieu/noi-bo/tai-lieu",
                json=jsonable_encoder(payload),
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        response.raise_for_status()
        return response.json().get("data")

    @classmethod
    def find(cls, query: dict, projection: dict = None, **kwargs):
        return DocumentCursor(query, projection)

    @classmethod
    async def find_one(cls, query: dict, projection: dict = None, **kwargs):
        return await cls.request(
            {"operation": "find_one", "query": query, "projection": projection}
        )
