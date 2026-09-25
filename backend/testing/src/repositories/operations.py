from src.core.database import database


class OperationsRepository:
    async def list_records(self, collection_name, query, sort_field, limit, projection=None):
        return await database.value[collection_name].find(query, projection).sort(
            sort_field, -1
        ).to_list(limit)

    async def count_records(self, collection_name, query):
        return await database.value[collection_name].count_documents(query)

    async def list_project_storage_values(
        self, collection_name, project_id, field, limit
    ):
        return await database.value[collection_name].find(
            {"project_id": project_id}, {field: 1}
        ).to_list(limit)

    async def average_impact_latency(self):
        return await database.value.impact_analyses.aggregate(
            [
                {"$match": {"ai_result.latency_ms": {"$type": "number"}}},
                {"$group": {"_id": None, "average_ms": {"$avg": "$ai_result.latency_ms"}}},
            ]
        ).to_list(1)


operations_repository = OperationsRepository()
