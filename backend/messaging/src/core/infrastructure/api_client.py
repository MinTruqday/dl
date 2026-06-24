
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

    async def find_one(self, collection: str, query: dict, projection: dict = None):
        res = await self._post("/find_one", {"db": "doclib", "collection": collection, "query": query, "projection": projection})
        return res.get("data")

    async def find(self, collection: str, query: dict, projection: dict = None, sort=None, skip: int = 0, limit: int = 0):
        res = await self._post("/find", {
            "db": "doclib",
            "collection": collection,
            "query": query,
            "projection": projection,
            "sort": sort,
            "skip": skip,
            "limit": limit
        })
        return res.get("data", [])

    async def insert_one(self, collection: str, document: dict):
        class InsertOneResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        res = await self._post("/insert_one", {"db": "doclib", "collection": collection, "document": document})
        return InsertOneResult(res.get("inserted_id"))

    async def update_one(self, collection: str, filter: dict, update: dict, upsert: bool = False):
        class UpdateResult:
            def __init__(self, matched_count, modified_count, upserted_id):
                self.matched_count = matched_count
                self.modified_count = modified_count
                self.upserted_id = upserted_id
        res = await self._post("/update_one", {"db": "doclib", "collection": collection, "filter": filter, "update": update, "upsert": upsert})
        return UpdateResult(res.get("matched_count"), res.get("modified_count"), res.get("upserted_id"))

    async def update_many(self, collection: str, filter: dict, update: dict, upsert: bool = False):
        class UpdateResult:
            def __init__(self, matched_count, modified_count, upserted_id):
                self.matched_count = matched_count
                self.modified_count = modified_count
                self.upserted_id = upserted_id
        res = await self._post("/update_many", {"db": "doclib", "collection": collection, "filter": filter, "update": update, "upsert": upsert})
        return UpdateResult(res.get("matched_count"), res.get("modified_count"), res.get("upserted_id"))

    async def delete_one(self, collection: str, filter: dict):
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        res = await self._post("/delete_one", {"db": "doclib", "collection": collection, "filter": filter})
        return DeleteResult(res.get("deleted_count"))

    async def delete_many(self, collection: str, filter: dict):
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        res = await self._post("/delete_many", {"db": "doclib", "collection": collection, "filter": filter})
        return DeleteResult(res.get("deleted_count"))

    async def count_documents(self, collection: str, filter: dict = {}):
        res = await self._post("/count_documents", {"db": "doclib", "collection": collection, "filter": filter})
        return res.get("count", 0)

    async def aggregate(self, collection: str, pipeline: list):
        res = await self._post("/aggregate", {"db": "doclib", "collection": collection, "pipeline": pipeline})
        return res.get("data", [])


class QueryBuilder:
    def __init__(self, client, collection: str):
        self.client = client
        self.collection = collection
        self._query = {}
        self._sort = None
        self._skip = 0
        self._limit = 0

    def filter(self, query: dict):
        self._query = query
        return self

    def sort(self, *args):
        if len(args) == 2 and isinstance(args[0], str):
            self._sort = [args]
        else:
            self._sort = args[0]
        return self

    def skip(self, s: int):
        self._skip = s
        return self

    def limit(self, l: int):
        self._limit = l
        return self

    async def execute(self):
        return await self.client.find(self.collection, self._query, sort=self._sort, skip=self._skip, limit=self._limit)

    def query(self, collection: str):
        return QueryBuilder(self, collection)

db_client = DatabaseAPIClient()
