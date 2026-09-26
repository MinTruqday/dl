from pymongo import ReturnDocument

from src.core.database import database


class CommonRepository:
    async def insert_audit_event(self, event):
        await database.value.audit_events.insert_one(event)
        return event

    async def find_project(self, project_id, projection=None):
        return await database.value.projects.find_one({"_id": project_id}, projection)

    async def find_membership(self, project_id, user_id, status=None, projection=None):
        query = {"project_id": project_id, "user_id": user_id}
        if status:
            query["status"] = status
        return await database.value.project_members.find_one(query, projection)

    async def find_active_grant(self, project_id, user_id, active_status, active_after):
        return await database.value.break_glass_grants.find_one(
            {
                "project_id": project_id,
                "user_id": user_id,
                "status": active_status,
                "expires_at": {"$gt": active_after},
            }
        )

    async def find_entity_identity(self, collection, entity_id, projection):
        return await database.value[collection].find_one({"_id": entity_id}, projection)

    async def find_project_entity(self, collection, entity_id, project_id):
        return await database.value[collection].find_one(
            {"_id": entity_id, "project_id": project_id}
        )

    async def optimistic_patch(
        self,
        collection,
        entity_id,
        project_id,
        expected_revision,
        changes,
        include_project_scope=True,
    ):
        scope = {"_id": entity_id, "revision": expected_revision}
        if include_project_scope:
            scope["project_id"] = project_id
        return await database.value[collection].find_one_and_update(
            scope,
            {"$set": changes, "$inc": {"revision": 1}},
            return_document=ReturnDocument.AFTER,
        )

    async def find_entity(self, collection, entity_id):
        return await database.value[collection].find_one({"_id": entity_id})

    async def next_counter(self, counter_id):
        return await database.value.counters.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"value": 1}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )


common_repository = CommonRepository()
