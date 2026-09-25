from pymongo import ReturnDocument

from src.core.database import database


class RequirementAnalysisRepository:
    async def list_versions(self, query, limit):
        return await database.value.requirement_versions.find(query).to_list(limit)

    async def list_requirements(self, query, limit=500):
        return await database.value.requirements.find(query).to_list(limit)

    async def list_acceptance_criteria(self, query, limit=10000):
        return await database.value.acceptance_criteria.find(query).to_list(limit)

    async def insert_duplicate_scan(self, value):
        await database.value.requirement_duplicate_scans.insert_one(value)
        return value

    async def find_requirement(self, requirement_id, project_id, projection=None):
        return await database.value.requirements.find_one(
            {"_id": requirement_id, "project_id": project_id}, projection
        )

    async def find_version(self, version_id, project_id, projection=None):
        return await database.value.requirement_versions.find_one(
            {"_id": version_id, "project_id": project_id}, projection
        )

    async def update_draft_dependencies(
        self,
        version_id,
        project_id,
        revision,
        dependencies,
        updated_at,
    ):
        return await database.value.requirement_versions.find_one_and_update(
            {
                "_id": version_id,
                "project_id": project_id,
                "status": "DRAFT",
                "revision": revision,
            },
            {
                "$set": {"dependencies": dependencies, "updated_at": updated_at},
                "$inc": {"revision": 1},
            },
            return_document=ReturnDocument.AFTER,
        )

    async def find_basis(self, collection_name, query, projection=None):
        return await database.value[collection_name].find_one(query, projection)

    async def list_basis(self, collection_name, query, limit):
        return await database.value[collection_name].find(query).limit(limit).to_list(limit)


requirement_analysis_repository = RequirementAnalysisRepository()
