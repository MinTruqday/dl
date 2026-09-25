from src.core.database import database


class TestPlanRepository:
    async def find_strategy(self, project_id, strategy_version_id):
        return await database.value.test_strategies.find_one(
            {"_id": strategy_version_id, "project_id": project_id}
        )

    async def find_active_strategy(self, project_id, approved_status):
        return await database.value.test_strategies.find_one(
            {
                "project_id": project_id,
                "status": approved_status,
                "active_approved": True,
            }
        )

    async def insert_plan(self, value):
        await database.value.test_plans.insert_one(value)
        return value

    async def list_plans(self, query, sort_field, direction, limit):
        return await database.value.test_plans.find(query).sort(
            sort_field, direction
        ).to_list(limit)

    async def find_project_settings(self, project_id):
        project = await database.value.projects.find_one(
            {"_id": project_id}, {"settings": 1}
        )
        return (project or {}).get("settings") or {}


test_plan_repository = TestPlanRepository()
