from pymongo import ReturnDocument

from src.core.database import database


class RequirementImportRepository:
    async def find_by_source_document(self, document_id):
        return await database.value.import_jobs.find_one(
            {"source_document_id": document_id}
        )

    async def find(self, job_id, project_id):
        return await database.value.import_jobs.find_one(
            {"_id": job_id, "project_id": project_id}
        )

    async def insert(self, job):
        await database.value.import_jobs.insert_one(job)

    async def mark_document_extracted(
        self, document_id, project_id, status, job_id, updated_at
    ):
        await database.value.requirement_documents.update_one(
            {"_id": document_id, "project_id": project_id},
            {
                "$set": {
                    "status": status,
                    "last_import_job_id": job_id,
                    "updated_at": updated_at,
                },
                "$inc": {"revision": 1},
            },
        )

    async def update_preview(
        self,
        job_id,
        project_id,
        status,
        revision,
        preview,
        user_id,
        updated_at,
        review_note=None,
        push_field=None,
        push_value=None,
    ):
        changes = {
            "preview": preview,
            "candidate_count": len(preview),
            "reviewed_by": user_id,
            "reviewed_at": updated_at,
            "updated_at": updated_at,
        }
        if review_note is not None:
            changes["review_note"] = review_note
        update = {"$set": changes, "$inc": {"revision": 1}}
        if push_field:
            update["$push"] = {push_field: push_value}
        return await database.value.import_jobs.find_one_and_update(
            {
                "_id": job_id,
                "project_id": project_id,
                "status": status,
                "revision": revision,
            },
            update,
            return_document=ReturnDocument.AFTER,
        )

    async def claim_confirmation(
        self,
        job_id,
        project_id,
        source_status,
        target_status,
        user_id,
        updated_at,
        revision=None,
    ):
        query = {"_id": job_id, "project_id": project_id, "status": source_status}
        if revision is not None:
            query["revision"] = revision
        result = await database.value.import_jobs.update_one(
            query,
            {
                "$set": {
                    "status": target_status,
                    "confirming_by": user_id,
                    "updated_at": updated_at,
                },
                "$inc": {"revision": 1},
            },
        )
        return result.matched_count == 1

    async def delete_created_requirements(self, requirement_ids, version_ids):
        if not requirement_ids:
            return
        await database.value.acceptance_criteria.delete_many(
            {"requirement_version_id": {"$in": version_ids}}
        )
        await database.value.requirement_versions.delete_many(
            {"_id": {"$in": version_ids}}
        )
        await database.value.requirements.delete_many(
            {"_id": {"$in": requirement_ids}}
        )

    async def reset_confirmation(
        self, job_id, project_id, source_status, target_status, updated_at
    ):
        await database.value.import_jobs.update_one(
            {"_id": job_id, "project_id": project_id, "status": source_status},
            {
                "$set": {"status": target_status, "updated_at": updated_at},
                "$inc": {"revision": 1},
            },
        )

    async def confirm(
        self,
        job_id,
        project_id,
        source_status,
        target_status,
        requirement_ids,
        selected_indexes,
        rejected_indexes,
        user_id,
        updated_at,
    ):
        await database.value.import_jobs.update_one(
            {"_id": job_id, "project_id": project_id, "status": source_status},
            {
                "$set": {
                    "status": target_status,
                    "created_requirement_ids": requirement_ids,
                    "selected_indexes": selected_indexes,
                    "rejected_indexes": rejected_indexes,
                    "confirmed_at": updated_at,
                    "confirmed_by": user_id,
                    "updated_at": updated_at,
                },
                "$inc": {"revision": 1},
            },
        )

    async def confirm_document(self, document_id, project_id, status, updated_at):
        await database.value.requirement_documents.update_one(
            {"_id": document_id, "project_id": project_id},
            {
                "$set": {"status": status, "updated_at": updated_at},
                "$inc": {"revision": 1},
            },
        )


requirement_import_repository = RequirementImportRepository()
