from src.core.database import database


class AnalyticsRepository:
    async def list_records(self, collection, query, limit, sort=None, projection=None):
        cursor = database.value[collection].find(query, projection)
        if sort:
            cursor = cursor.sort(*sort)
        return await cursor.limit(limit).to_list(limit)

    async def count_records(self, collection, query):
        return await database.value[collection].count_documents(query)

    async def group_counts(self, collection, match, field, limit):
        return await database.value[collection].aggregate(
            [
                {"$match": match},
                {"$group": {"_id": f"${field}", "count": {"$sum": 1}}},
            ]
        ).to_list(limit)

    async def find_latest(self, collection, query, sort_field="updated_at"):
        return await database.value[collection].find_one(
            query, sort=[(sort_field, -1)]
        )

    async def insert_ai_audit(self, value):
        await database.value.ai_request_audit.insert_one(value)


analytics_repository = AnalyticsRepository()
