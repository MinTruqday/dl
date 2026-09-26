from pymongo import ReturnDocument

from src.core.database import database


class ProjectNotificationRepository:
    @property
    def subscriptions(self):
        return database.value.notification_subscriptions

    @property
    def rules(self):
        return database.value.project_notification_rules

    @property
    def preferences(self):
        return database.value.project_notification_preferences

    async def artifact_exists(self, collection_name, project_id, artifact_id):
        return bool(
            await database.value[collection_name].find_one(
                {"_id": artifact_id, "project_id": project_id},
                {"_id": 1},
            )
        )

    async def list_subscriptions(self, query, limit=1000):
        return await self.subscriptions.find(query).sort("updated_at", -1).to_list(limit)

    async def list_artifact_labels(self, collection_name, project_id, identifiers):
        return await database.value[collection_name].find(
            {"project_id": project_id, "_id": {"$in": identifiers}},
            {
                "_id": 1,
                "requirement_key": 1,
                "test_case_key": 1,
                "name": 1,
                "defect_key": 1,
                "title": 1,
            },
        ).to_list(len(identifiers))

    async def remove_subscription(self, scope):
        return await self.subscriptions.delete_one(scope)

    async def set_subscription(self, scope, subscription_id, timestamp):
        return await self.subscriptions.find_one_and_update(
            scope,
            {
                "$set": {"updated_at": timestamp},
                "$setOnInsert": {
                    "_id": subscription_id,
                    **scope,
                    "created_at": timestamp,
                },
            },
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )

    async def find_rules(self, project_id):
        return await self.rules.find_one({"project_id": project_id})

    async def insert_rules(self, value):
        await self.rules.insert_one(value)
        return value

    async def find_preferences(self, project_id, user_id):
        return await self.preferences.find_one(
            {"project_id": project_id, "user_id": user_id}
        )

    async def insert_preferences(self, value):
        await self.preferences.insert_one(value)
        return value


project_notification_repository = ProjectNotificationRepository()
