import httpx
from typing import Any, Dict, List, Optional
import os

class CollectionProxy:
    def __init__(self, db_name: str, collection_name: str):
        self.db_name = db_name
        self.collection_name = collection_name
        # Using the internal traefik router or docker network DNS
        self.base_url = "http://doclib_database:8800/mongo"

    async def _post(self, path: str, payload: dict):
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(f"{self.base_url}{path}", json=payload)
            if resp.status_code >= 400:
                raise Exception(f"Database error: {resp.text}")
            return resp.json()

    async def find_one(self, query: dict, projection: dict = None):
        res = await self._post("/find_one", {"db": self.db_name, "collection": self.collection_name, "query": query, "projection": projection})
        return res.get("data")

    def find(self, query: dict, projection: dict = None):
        return CursorProxy(self, query, projection)

    async def insert_one(self, document: dict):
        class InsertOneResult:
            def __init__(self, inserted_id):
                self.inserted_id = inserted_id
        res = await self._post("/insert_one", {"db": self.db_name, "collection": self.collection_name, "document": document})
        return InsertOneResult(res.get("inserted_id"))

    async def update_one(self, filter: dict, update: dict, upsert: bool = False):
        class UpdateResult:
            def __init__(self, matched_count, modified_count, upserted_id):
                self.matched_count = matched_count
                self.modified_count = modified_count
                self.upserted_id = upserted_id
        res = await self._post("/update_one", {"db": self.db_name, "collection": self.collection_name, "filter": filter, "update": update, "upsert": upsert})
        return UpdateResult(res.get("matched_count"), res.get("modified_count"), res.get("upserted_id"))

    async def update_many(self, filter: dict, update: dict, upsert: bool = False):
        class UpdateResult:
            def __init__(self, matched_count, modified_count, upserted_id):
                self.matched_count = matched_count
                self.modified_count = modified_count
                self.upserted_id = upserted_id
        res = await self._post("/update_many", {"db": self.db_name, "collection": self.collection_name, "filter": filter, "update": update, "upsert": upsert})
        return UpdateResult(res.get("matched_count"), res.get("modified_count"), res.get("upserted_id"))

    async def delete_one(self, filter: dict):
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        res = await self._post("/delete_one", {"db": self.db_name, "collection": self.collection_name, "filter": filter})
        return DeleteResult(res.get("deleted_count"))

    async def delete_many(self, filter: dict):
        class DeleteResult:
            def __init__(self, deleted_count):
                self.deleted_count = deleted_count
        res = await self._post("/delete_many", {"db": self.db_name, "collection": self.collection_name, "filter": filter})
        return DeleteResult(res.get("deleted_count"))

    async def count_documents(self, filter: dict = {}):
        res = await self._post("/count_documents", {"db": self.db_name, "collection": self.collection_name, "filter": filter})
        return res.get("count", 0)

    def aggregate(self, pipeline: list):
        return CursorProxy(self, pipeline=pipeline, is_aggregate=True)

    async def create_index(self, keys, **kwargs):
        # We can ignore create_index in other services since database service handles it, or pass it.
        pass

class CursorProxy:
    def __init__(self, collection: CollectionProxy, query: dict = None, projection: dict = None, pipeline: list = None, is_aggregate=False):
        self.collection = collection
        self.query = query or {}
        self.projection = projection
        self.pipeline = pipeline
        self.is_aggregate = is_aggregate
        self._sort = None
        self._skip = 0
        self._limit = 0
        self._results = None

    def sort(self, sort_list):
        self._sort = sort_list
        return self

    def skip(self, skip_val):
        self._skip = skip_val
        return self

    def limit(self, limit_val):
        self._limit = limit_val
        return self

    async def to_list(self, length=None):
        if self._results is None:
            if self.is_aggregate:
                res = await self.collection._post("/aggregate", {
                    "db": self.collection.db_name,
                    "collection": self.collection.collection_name,
                    "pipeline": self.pipeline
                })
            else:
                res = await self.collection._post("/find", {
                    "db": self.collection.db_name,
                    "collection": self.collection.collection_name,
                    "query": self.query,
                    "projection": self.projection,
                    "sort": self._sort,
                    "skip": self._skip,
                    "limit": self._limit or length or 0
                })
            self._results = res.get("data", [])
        return self._results

    def __aiter__(self):
        self._iter_index = 0
        return self

    async def __anext__(self):
        if self._results is None:
            await self.to_list()
        if self._iter_index < len(self._results):
            val = self._results[self._iter_index]
            self._iter_index += 1
            return val
        raise StopAsyncIteration

class DatabaseProxy:
    def __init__(self, db_name: str):
        self.db_name = db_name

    def __getattr__(self, name):
        return CollectionProxy(self.db_name, name)

    def __getitem__(self, name):
        return CollectionProxy(self.db_name, name)

class ClientProxy:
    def __getattr__(self, name):
        if name == "admin":
            class AdminProxy:
                async def command(self, *args, **kwargs):
                    return {}
            return AdminProxy()
        return DatabaseProxy(name)

    def __getitem__(self, name):
        return DatabaseProxy(name)

    def close(self):
        pass
