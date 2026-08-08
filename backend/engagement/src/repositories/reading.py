import httpx
from fastapi.encoders import jsonable_encoder
from src.core.infrastructure.mongo import mongo
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

class ReadingRepository:
    @classmethod
    async def update_history(cls, *args, **kwargs):
        return await mongo.update_one("reading_history", *args, **kwargs)

    @classmethod
    async def delete_historys(cls, *args, **kwargs):
        return await mongo.delete_many("reading_history", *args, **kwargs)

    @classmethod
    async def delete_history(cls, *args, **kwargs):
        return await mongo.delete_one("reading_history", *args, **kwargs)

    @classmethod
    async def update_list(cls, *args, **kwargs):
        return await mongo.update_one("reading_lists", *args, **kwargs)

    @classmethod
    async def insert_list(cls, *args, **kwargs):
        return await mongo.insert_one("reading_lists", *args, **kwargs)

    @classmethod
    async def find_list(cls, *args, **kwargs):
        return await mongo.find_one("reading_lists", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("reading_history", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("reading_history", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("reading_history", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("reading_history", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("reading_history", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("reading_history", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("reading_history", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("reading_history", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("reading_history", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("reading_history", *args, **kwargs)

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
    async def find_one(cls, query: dict, projection: dict = None, **kwargs):
        return await cls.request(
            {"operation": "find_one", "query": query, "projection": projection}
        )

    @classmethod
    async def get_accessible(cls, document_id: str, user_id: str, is_admin: bool):
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{settings.CONTENT_URL}/tai-lieu/noi-bo/truy-cap",
                json={
                    "document_id": document_id,
                    "user_id": user_id,
                    "is_admin": is_admin,
                    "edit": False,
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.json().get("data")

    @classmethod
    async def taxonomy(cls):
        return await cls.request({"operation": "taxonomy"})

    @classmethod
    def find(cls, query: dict, projection: dict = None, **kwargs):
        return DocumentCursor(query, projection)
