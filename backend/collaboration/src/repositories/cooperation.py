import httpx
from fastapi.encoders import jsonable_encoder
from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.configuration import settings

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
    async def update_one(cls, query: dict, update: dict, upsert: bool = False, **kwargs):
        return await cls.request(
            {
                "operation": "update_one",
                "query": query,
                "update": update,
                "upsert": upsert,
            }
        )

class CooperationRepository:
    @classmethod
    async def insert_activity(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def insert_draft(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_drafts", *args, **kwargs)

    @classmethod
    async def update_invite(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_invites", *args, **kwargs)

    @classmethod
    async def delete_invite(cls, *args, **kwargs):
        return await mongo.delete_one("collaboration_invites", *args, **kwargs)

    @classmethod
    async def insert_invite(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_invites", *args, **kwargs)

    @classmethod
    async def find_invite(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_invites", *args, **kwargs)

    @classmethod
    async def find_invites(cls, query: dict):
        return await mongo.find("collaboration_invites", query).to_list(length=None)

    @classmethod
    async def update_invite_code(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_invite_codes", *args, **kwargs)

    @classmethod
    async def find_invite_code(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_invite_codes", *args, **kwargs)

    @classmethod
    async def update_lock(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_locks", *args, **kwargs)

    @classmethod
    async def delete_lock(cls, *args, **kwargs):
        return await mongo.delete_one("collaboration_locks", *args, **kwargs)

    @classmethod
    async def find_lock(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_locks", *args, **kwargs)

    @classmethod
    async def insert_memo(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_memos", *args, **kwargs)

    @classmethod
    async def update_status(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_status", *args, **kwargs)

    @classmethod
    async def update_task(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_tasks", *args, **kwargs)

    @classmethod
    async def insert_task(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_tasks", *args, **kwargs)

    @classmethod
    async def find_task(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_tasks", *args, **kwargs)

    @classmethod
    async def insert_task_comment(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_task_comments", *args, **kwargs)

    @classmethod
    async def insert_one(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def insert_many(cls, *args, **kwargs):
        return await mongo.insert_many("collaboration_activities", *args, **kwargs)

    @classmethod
    async def find_one(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def update_one(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def update_many(cls, *args, **kwargs):
        return await mongo.update_many("collaboration_activities", *args, **kwargs)

    @classmethod
    async def delete_one(cls, *args, **kwargs):
        return await mongo.delete_one("collaboration_activities", *args, **kwargs)

    @classmethod
    async def delete_many(cls, *args, **kwargs):
        return await mongo.delete_many("collaboration_activities", *args, **kwargs)

    @classmethod
    async def count_documents(cls, *args, **kwargs):
        return await mongo.count_documents("collaboration_activities", *args, **kwargs)

    @classmethod
    def find(cls, *args, **kwargs):
        return mongo.find("collaboration_activities", *args, **kwargs)

    @classmethod
    def aggregate(cls, *args, **kwargs):
        return mongo.aggregate("collaboration_activities", *args, **kwargs)

    @classmethod
    async def find_share_link(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_share_links", *args, **kwargs)

    @classmethod
    async def update_share_link(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_share_links", *args, **kwargs)

    @classmethod
    async def insert_access_request(cls, *args, **kwargs):
        return await mongo.insert_one("collaboration_access_requests", *args, **kwargs)

    @classmethod
    async def find_access_request(cls, *args, **kwargs):
        return await mongo.find_one("collaboration_access_requests", *args, **kwargs)

    @classmethod
    def find_access_requests(cls, *args, **kwargs):
        return mongo.find("collaboration_access_requests", *args, **kwargs)

    @classmethod
    async def update_access_request(cls, *args, **kwargs):
        return await mongo.update_one("collaboration_access_requests", *args, **kwargs)
