from pymongo import ReturnDocument

from src.core.database import database


class RequirementAiRepository:
    async def find_finding(self, query):
        return await database.value.ai_findings.find_one(query)

    async def list_acceptance_criteria(self, version_id, limit):
        return await database.value.acceptance_criteria.find(
            {"requirement_version_id": version_id}
        ).to_list(limit)

    async def insert_finding(self, value):
        await database.value.ai_findings.insert_one(value)
        return value

    async def update_requirement(self, query, changes):
        return await database.value.requirement_versions.find_one_and_update(
            query,
            {"$set": changes, "$inc": {"revision": 1}},
            return_document=ReturnDocument.AFTER,
        )

    async def delete_acceptance_criteria(self, version_id):
        await database.value.acceptance_criteria.delete_many(
            {"requirement_version_id": version_id}
        )

    async def insert_acceptance_criteria(self, values):
        if values:
            await database.value.acceptance_criteria.insert_many(values)

    async def rollback_requirement(self, query, values, missing_fields):
        update = {"$set": values}
        if missing_fields:
            update["$unset"] = {field: "" for field in missing_fields}
        await database.value.requirement_versions.update_one(query, update)

    async def find_requirement_version(self, version_id):
        return await database.value.requirement_versions.find_one({"_id": version_id})

    async def mark_suggestion_applied(self, finding_id, project_id, suggestion_id, updated_at):
        await database.value.ai_findings.update_one(
            {"_id": finding_id, "project_id": project_id},
            {
                "$addToSet": {"applied_suggestion_ids": suggestion_id},
                "$set": {"updated_at": updated_at},
            },
        )


requirement_ai_repository = RequirementAiRepository()
