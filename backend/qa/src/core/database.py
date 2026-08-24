from motor.motor_asyncio import AsyncIOMotorClient

from src.core.configuration import settings


class Database:
    client: AsyncIOMotorClient | None = None

    @property
    def value(self):
        if self.client is None:
            raise RuntimeError("Cơ sở dữ liệu chưa sẵn sàng")
        return self.client[settings.QA_DB_NAME]


database = Database()


async def connect_database():
    database.client = AsyncIOMotorClient(settings.MONGODB_URI, tz_aware=True)
    await database.client.admin.command("ping")
    await create_indexes()


async def close_database():
    if database.client is not None:
        database.client.close()
        database.client = None


async def create_indexes():
    db = database.value
    await db.projects.create_index("key", unique=True)
    await db.projects.create_index([("owner_id", 1), ("updated_at", -1)])
    await db.requirements.create_index([("project_id", 1), ("requirement_key", 1)], unique=True)
    await db.requirement_versions.create_index([("requirement_id", 1), ("version", 1)], unique=True)
    await db.acceptance_criteria.create_index([("requirement_version_id", 1), ("key", 1)], unique=True)
    await db.test_scenarios.create_index([("project_id", 1), ("scenario_key", 1)], unique=True)
    await db.test_case_drafts.create_index([("project_id", 1), ("updated_at", -1)])
    await db.test_cases.create_index([("project_id", 1), ("test_case_key", 1)], unique=True)
    await db.test_case_versions.create_index([("test_case_id", 1), ("version", 1)], unique=True)
    await db.trace_links.create_index([("project_id", 1), ("source_type", 1), ("source_id", 1)])
    await db.trace_links.create_index([("project_id", 1), ("target_type", 1), ("target_id", 1)])
    await db.requirement_change_sets.create_index([("requirement_id", 1), ("to_version_id", 1)], unique=True)
    await db.impact_analyses.create_index([("project_id", 1), ("change_set_id", 1), ("created_at", -1)])
    await db.maintenance_proposals.create_index([("project_id", 1), ("status", 1)])
    await db.test_plans.create_index([("project_id", 1), ("updated_at", -1)])
    await db.test_suites.create_index([("project_id", 1), ("updated_at", -1)])
    await db.test_runs.create_index([("project_id", 1), ("status", 1), ("updated_at", -1)])
    await db.test_results.create_index([("test_run_id", 1), ("test_case_version_id", 1)], unique=True)
    await db.defects.create_index([("project_id", 1), ("defect_key", 1)], unique=True)
    await db.audit_events.create_index([("project_id", 1), ("created_at", -1)])
    await db.import_jobs.create_index([("project_id", 1), ("created_at", -1)])
    await db.api_imports.create_index([("project_id", 1), ("created_at", -1)])
    await db.api_operations.create_index([("project_id", 1), ("method", 1), ("path", 1)])
    await db.test_imports.create_index([("project_id", 1), ("created_at", -1)])
    await db.worker_events.create_index([("project_id", 1), ("event", 1), ("completed_at", -1)])
