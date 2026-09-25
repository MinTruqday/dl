from typing import Any

from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.infrastructure.mongo import mongo


class DocumentRepository:
    @staticmethod
    def normalize_query(value: Any) -> Any:
        if isinstance(value, list):
            return [DocumentRepository.normalize_query(item) for item in value]
        if not isinstance(value, dict):
            return value
        normalized = {}
        for key, item in value.items():
            if key == "_id" and isinstance(item, str) and ObjectId.is_valid(item):
                normalized[key] = {"$in": [item, ObjectId(item)]}
            else:
                normalized[key] = DocumentRepository.normalize_query(item)
        return normalized

    @staticmethod
    def identifiers(values: list[str]):
        return values + [ObjectId(value) for value in values if ObjectId.is_valid(value)]

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("documents", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("documents", *args, **kwargs)

    @classmethod
    async def insert_revision(cls, *args, **kwargs):
        return await mongo.insert_one("document_revisions", *args, **kwargs)

    @classmethod
    async def insert_version(cls, *args, **kwargs):
        return await mongo.insert_one("document_versions", *args, **kwargs)

    @classmethod
    async def find_version(cls, *args, **kwargs):
        return await mongo.find_one("document_versions", *args, **kwargs)

    @classmethod
    def find_versions(cls, *args, **kwargs):
        return mongo.find("document_versions", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("documents", *args, **kwargs)

    @classmethod
    async def insert_one_if_unique(cls, document: dict):
        try:
            await mongo.insert_one("documents", document)
            return True
        except DuplicateKeyError:
            return False

    @classmethod
    async def find_one_and_update(cls, query: dict, update: dict, upsert: bool = False):
        return await mongo.get_db()["documents"].find_one_and_update(
            query,
            update,
            upsert=upsert,
            return_document=ReturnDocument.AFTER,
        )

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("documents", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("documents", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("documents", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("documents", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("documents", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("documents", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("documents", *args, **kwargs)

    @classmethod
    def query(cls, *args, **kwargs):
        return mongo.query("documents", *args, **kwargs)
