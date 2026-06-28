from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database

class MockCursor:
    def __init__(self, cursor):
        self._cursor = cursor
    def limit(self, limit):
        self._cursor = self._cursor.limit(limit)
        return self
    def skip(self, skip):
        self._cursor = self._cursor.skip(skip)
        return self
    def sort(self, *args, **kwargs):
        self._cursor = self._cursor.sort(*args, **kwargs)
        return self
    def execute(self):
        return self._cursor.to_list(length=None)
    def __await__(self):
        return self._cursor.to_list(length=None).__await__()

class MockPipeline:
    def __init__(self, motor_pipeline):
        self._motor_pipeline = motor_pipeline

    def execute(self):
        return self

    def __await__(self):
        return self._motor_pipeline.to_list(length=None).__await__()

try:
    from motor.motor_asyncio import AsyncIOMotorCursor, AsyncIOMotorCommandCursor
    def _cursor_await(self):
        return self.to_list(length=None).__await__()
    AsyncIOMotorCursor.__await__ = _cursor_await
    AsyncIOMotorCommandCursor.__await__ = _cursor_await
except ImportError:
    pass

class MongoClient:
    def __init__(self):
        self.db_name = settings.SERVICE_DB_NAME

    def get_db(self):
        if not database.mongodb:
            raise Exception("MongoDB is not initialized")
        return database.mongodb[self.db_name]

    async def find_one(self, collection: str, query: dict, projection: dict = None, **kwargs):
        return await self.get_db()[collection].find_one(query, projection, **kwargs)

    def find(self, collection: str, query: dict, projection: dict = None, sort=None, skip: int = 0, limit: int = 0):
        cursor = self.get_db()[collection].find(query, projection)
        if sort:
            cursor = cursor.sort(sort)
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
        return MockCursor(cursor)

    def aggregate(self, collection: str, pipeline: list):
        cursor = self.get_db()[collection].aggregate(pipeline)
        return MockPipeline(cursor)

    async def insert_one(self, collection: str, document: dict, **kwargs):
        return await self.get_db()[collection].insert_one(document, **kwargs)

    async def insert_many(self, collection: str, documents: list):
        return await self.get_db()[collection].insert_many(documents)

    async def update_one(self, collection: str, filter: dict, update: dict, upsert: bool = False):
        return await self.get_db()[collection].update_one(filter, update, upsert=upsert)

    async def update_many(self, collection: str, filter: dict, update: dict, upsert: bool = False):
        return await self.get_db()[collection].update_many(filter, update, upsert=upsert)

    async def delete_one(self, collection: str, filter: dict):
        return await self.get_db()[collection].delete_one(filter)

    async def delete_many(self, collection: str, filter: dict):
        return await self.get_db()[collection].delete_many(filter)

    async def count_documents(self, collection: str, filter: dict = {}):
        return await self.get_db()[collection].count_documents(filter)

    def query(self, collection: str):
        return QueryBuilder(self, collection)

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

mongo = MongoClient()
