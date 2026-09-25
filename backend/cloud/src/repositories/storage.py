import json
from typing import Any, Optional

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.redis import redis


class StorageRepository:
    @property
    def collection(self):
        return database.mongodb[settings.CLOUD_DB_NAME].storage_items

    async def find_one(self, query: dict, projection: Optional[dict] = None):
        return await self.collection.find_one(query, projection)

    async def find_many(
        self,
        query: dict,
        projection: Optional[dict] = None,
        sort: Optional[list] = None,
        limit: Optional[int] = None,
    ) -> list[dict]:
        cursor = self.collection.find(query, projection)
        if sort:
            cursor = cursor.sort(sort)
        if limit is not None:
            cursor = cursor.limit(limit)
        return await cursor.to_list(length=limit)

    async def insert(self, document: dict):
        return await self.collection.insert_one(document)

    async def update_one(self, query: dict, update: dict):
        return await self.collection.update_one(query, update)

    async def update_many(self, query: dict, update: dict):
        return await self.collection.update_many(query, update)

    async def find_one_and_update(self, query: dict, update: dict):
        return await self.collection.find_one_and_update(
            query,
            update,
            return_document=True,
        )

    async def delete_one(self, query: dict):
        return await self.collection.delete_one(query)

    async def delete_many(self, query: dict):
        return await self.collection.delete_many(query)

    async def count(self, query: dict) -> int:
        return await self.collection.count_documents(query)

    async def aggregate(self, pipeline: list[dict]) -> list[dict]:
        return await self.collection.aggregate(pipeline).to_list(length=None)

    async def replace_version(
        self,
        item_id: str,
        owner_id: str,
        update: dict,
        registered_id: Optional[Any],
    ) -> None:
        async with await database.mongodb.start_session() as session:
            async with session.start_transaction():
                await self.collection.update_one(
                    {"_id": item_id, "owner_id": owner_id},
                    update,
                    session=session,
                )
                if registered_id is not None and str(registered_id) != item_id:
                    await self.collection.delete_one(
                        {"_id": registered_id, "owner_id": owner_id},
                        session=session,
                    )


class ActivityRepository:
    @property
    def collection(self):
        return database.mongodb[settings.CLOUD_DB_NAME].storage_activities

    async def insert(self, document: dict):
        return await self.collection.insert_one(document)

    async def list_for_item(self, item_id: str, limit: int) -> list[dict]:
        cursor = self.collection.find({"item_id": item_id}).sort([("timestamp", -1)]).limit(limit)
        return await cursor.to_list(length=limit)


class ShareLinkRepository:
    @property
    def collection(self):
        return database.mongodb[settings.CLOUD_DB_NAME].storage_share_links

    async def insert(self, document: dict):
        return await self.collection.insert_one(document)

    async def find(self, token: str):
        return await self.collection.find_one({"_id": token})

    async def delete(self, token: str):
        return await self.collection.delete_one({"_id": token})


class FileRequestRepository:
    @property
    def collection(self):
        return database.mongodb[settings.CLOUD_DB_NAME].file_requests

    async def insert(self, document: dict):
        return await self.collection.insert_one(document)

    async def find(self, token: str):
        return await self.collection.find_one({"token": token})


class TemporaryFileRepository:
    @property
    def collection(self):
        return database.mongodb[settings.CLOUD_DB_NAME].temp_chat_files

    async def insert(self, document: dict):
        return await self.collection.insert_one(document)


class UploadReservationRepository:
    @staticmethod
    def key(file_path: str) -> str:
        return f"cloud:upload:{file_path}"

    async def reserve(self, file_path: str, ttl_seconds: int, reservation: dict) -> None:
        await redis.setex(self.key(file_path), ttl_seconds, json.dumps(reservation))

    async def consume(self, file_path: str):
        return await redis.get_client().execute_command("GETDEL", self.key(file_path))


storage_repository = StorageRepository()
activity_repository = ActivityRepository()
share_link_repository = ShareLinkRepository()
file_request_repository = FileRequestRepository()
temporary_file_repository = TemporaryFileRepository()
upload_reservation_repository = UploadReservationRepository()
