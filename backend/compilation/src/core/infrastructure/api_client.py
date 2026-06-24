
import httpx
from typing import Any, Dict, List, Optional

class DatabaseAPIClient:
    def __init__(self, base_url: str = "http://doclib_database:8800/mongo"):
        self.base_url = base_url

    async def _post(self, path: str, payload: dict):
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}{path}", json=payload)
            if resp.status_code >= 400:
                raise Exception(f"Database API error: {resp.text}")
            return resp.json()

    async def find_one(self, db: str, collection: str, query: dict, projection: dict = None):
        res = await self._post("/find_one", {"db": db, "collection": collection, "query": query, "projection": projection})
        return res.get("data")

    async def find(self, db: str, collection: str, query: dict, projection: dict = None, sort=None, skip: int = 0, limit: int = 0):
        res = await self._post("/find", {
            "db": db,
            "collection": collection,
            "query": query,
            "projection": projection,
            "sort": sort,
            "skip": skip,
            "limit": limit
        })
        return res.get("data", [])

    async def insert_one(self, db: str, collection: str, document: dict):
        class InsertOneResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        res = await self._post("/insert_one", {"db": db, "collection": collection, "document": document})
        return InsertOneResult(res.get("inserted_id"))

    async def update_one(self, db: str, collection: str, filter: dict, update: dict, upsert: bool = False):
        class UpdateResult:
            def __init__(self, matched_count, modified_count, upserted_id):
                self.matched_count = matched_count
                self.modified_count = modified_count
                self.upserted_id = upserted_id
        res = await self._post("/update_one", {"db": db, "collection": collection, "filter": filter, "update": update, "upsert": upsert})
        return UpdateResult(res.get("matched_count"), res.get("modified_count"), res.get("upserted_id"))

    async def update_many(self, db: str, collection: str, filter: dict, update: dict, upsert: bool = False):
        class UpdateResult:
            def __init__(self, matched_count, modified_count, upserted_id):
                self.matched_count = matched_count
                self.modified_count = modified_count
                self.upserted_id = upserted_id
        res = await self._post("/update_many", {"db": db, "collection": collection, "filter": filter, "update": update, "upsert": upsert})
        return UpdateResult(res.get("matched_count"), res.get("modified_count"), res.get("upserted_id"))

    async def delete_one(self, db: str, collection: str, filter: dict):
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        res = await self._post("/delete_one", {"db": db, "collection": collection, "filter": filter})
        return DeleteResult(res.get("deleted_count"))

    async def delete_many(self, db: str, collection: str, filter: dict):
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        res = await self._post("/delete_many", {"db": db, "collection": collection, "filter": filter})
        return DeleteResult(res.get("deleted_count"))

    async def count_documents(self, db: str, collection: str, filter: dict = {}):
        res = await self._post("/count_documents", {"db": db, "collection": collection, "filter": filter})
        return res.get("count", 0)

    async def aggregate(self, db: str, collection: str, pipeline: list):
        res = await self._post("/aggregate", {"db": db, "collection": collection, "pipeline": pipeline})
        return res.get("data", [])

db_client = DatabaseAPIClient()
