from datetime import timedelta

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.domain.contracts import CollaborationOperationInput, RequirementDraftPatch, TestCaseDraftPatch
from src.repositories.collaboration import collaboration_repository
from src.services.domain_policy import domain_policy
from src.services.requirement_records import update_requirement_draft_record
from src.services.test_case_records import update_test_case_draft_record


async def artifact_context(project_id, artifact_type, artifact_id, user, edit=False):
    policy = domain_policy("collaboration")
    if artifact_type == policy["requirement_artifact_type"]:
        requirement = await get_project_entity(
            "requirements", artifact_id, user, "requirement.update" if edit else "requirement.read"
        )
        if requirement["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
        version = await collaboration_repository.find_requirement_version(
            requirement["current_version_id"], project_id
        )
        if not version:
            raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
        if edit and version.get("status") != policy["draft_status"]:
            raise HTTPException(
                status_code=409, detail={"code": policy["immutable_requirement_code"]}
            )
        return version
    draft = await get_project_entity(
        "test_case_drafts", artifact_id, user, "testcase.update" if edit else "testcase.read"
    )
    if draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    if edit and draft.get("status") != policy["draft_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["immutable_test_case_code"]}
        )
    return draft


class CollaborationService:
    @staticmethod
    async def update_presence(project_id, payload, user):
        policy = domain_policy("collaboration")
        await get_project(project_id, user, "collaboration.presence.read")
        await artifact_context(project_id, payload.artifact_type, payload.artifact_id, user)
        timestamp = now()
        return await collaboration_repository.upsert_presence(
            {
                "project_id": project_id,
                "artifact_type": payload.artifact_type,
                "artifact_id": payload.artifact_id,
                "user_id": user.id,
                "client_id": payload.client_id,
            },
            {
                "user_email": user.email,
                "last_seen_at": timestamp,
                "expires_at": timestamp + timedelta(seconds=policy["presence_ttl_seconds"]),
            },
            {"_id": new_id(policy["presence_id_prefix"]), "created_at": timestamp},
        )

    @staticmethod
    async def list_presence(project_id, artifact_type, artifact_id, user):
        policy = domain_policy("collaboration")
        await get_project(project_id, user, "collaboration.presence.read")
        await artifact_context(project_id, artifact_type, artifact_id, user)
        return await collaboration_repository.list_presence(
            {
                "project_id": project_id,
                "artifact_type": artifact_type,
                "artifact_id": artifact_id,
                "expires_at": {"$gt": now()},
            },
            policy["presence_limit"],
        )

    @staticmethod
    async def apply_operation(project_id, artifact_type, artifact_id, payload, user):
        policy = domain_policy("collaboration")
        current = await artifact_context(project_id, artifact_type, artifact_id, user, edit=True)
        existing = await collaboration_repository.find_operation(
            project_id, payload.operation_id
        )
        if existing:
            return existing["result"]
        current_revision = current["revision"]
        changes = payload.changes
        rebased = False
        if payload.base_revision != current_revision:
            operations = await collaboration_repository.list_operations_since(
                project_id,
                artifact_type,
                artifact_id,
                payload.base_revision,
                policy["operation_history_limit"],
            )
            changed_keys = {
                key for operation in operations for key in operation.get("changed_keys", [])
            }
            if changed_keys.isdisjoint(changes):
                rebased = True
            else:
                conflict = {
                    "_id": new_id(policy["conflict_id_prefix"]),
                    "project_id": project_id,
                    "artifact_type": artifact_type,
                    "artifact_id": artifact_id,
                    "base_revision": payload.base_revision,
                    "current_revision": current_revision,
                    "incoming_changes": changes,
                    "changed_keys_since_base": sorted(changed_keys),
                    "operation_id": payload.operation_id,
                    "status": policy["open_status"],
                    "revision": 1,
                    "created_by": user.id,
                    "created_at": now(),
                    "updated_at": now(),
                }
                await collaboration_repository.insert_conflict(conflict)
                raise HTTPException(
                    status_code=409,
                    detail={
                        "code": policy["conflict_review_code"],
                        "conflict_id": conflict["_id"],
                    },
                )
        try:
            if artifact_type == policy["requirement_artifact_type"]:
                updated = await update_requirement_draft_record(
                    project_id,
                    artifact_id,
                    RequirementDraftPatch(expected_revision=current_revision, **changes),
                    user,
                )
                result = envelope(updated, revision=updated["current_version"]["revision"])
            else:
                updated = await update_test_case_draft_record(
                    artifact_id,
                    TestCaseDraftPatch(expected_revision=current_revision, **changes),
                    user,
                    project_id,
                )
                result = envelope(updated, revision=updated["revision"])
        except HTTPException as error:
            if error.status_code != 409:
                raise
            raise HTTPException(
                status_code=409,
                detail={"code": policy["retry_required_code"]},
            ) from error
        record = {
            "_id": new_id(policy["operation_id_prefix"]),
            "project_id": project_id,
            "artifact_type": artifact_type,
            "artifact_id": artifact_id,
            "operation_id": payload.operation_id,
            "base_revision": payload.base_revision,
            "result_revision": result["meta"]["revision"],
            "changed_keys": sorted(changes),
            "rebased": rebased,
            "result": result,
            "created_by": user.id,
            "created_at": now(),
        }
        try:
            await collaboration_repository.insert_operation(record)
        except DuplicateKeyError:
            existing = await collaboration_repository.find_operation(
                project_id, payload.operation_id
            )
            if existing:
                return existing["result"]
            raise
        await audit(
            user.id,
            "collaboration_operation_applied",
            "CollaborationSession",
            record["_id"],
            project_id,
            {"artifact_type": artifact_type, "artifact_id": artifact_id, "rebased": rebased},
        )
        return result

    @staticmethod
    async def list_conflicts(project_id, user):
        policy = domain_policy("collaboration")
        await get_project(project_id, user, "collaboration.conflict.resolve")
        return await collaboration_repository.list_conflicts(
            project_id, policy["conflict_limit"]
        )

    @classmethod
    async def resolve_conflict(cls, project_id, conflict_id, payload, user):
        policy = domain_policy("collaboration")
        conflict = await get_project_entity(
            "draft_conflicts", conflict_id, user, "collaboration.conflict.resolve"
        )
        if conflict["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
        current = await artifact_context(
            project_id, conflict["artifact_type"], conflict["artifact_id"], user, edit=True
        )
        if current["revision"] != payload.expected_revision:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": policy["revision_conflict_code"],
                    "current_revision": current["revision"],
                },
            )
        changes = (
            {}
            if payload.resolution == policy["keep_current_resolution"]
            else conflict["incoming_changes"]
            if payload.resolution == policy["apply_incoming_resolution"]
            else payload.merged_changes
        )
        result = None
        if changes:
            result = await cls.apply_operation(
                project_id,
                conflict["artifact_type"],
                conflict["artifact_id"],
                CollaborationOperationInput(
                    base_revision=current["revision"],
                    operation_id=f"resolve-{conflict_id}-{current['revision']}",
                    changes=changes,
                ),
                user,
            )
        timestamp = now()
        updated = await collaboration_repository.resolve_conflict(
            conflict_id,
            project_id,
            policy["open_status"],
            conflict["revision"],
            {
                "status": policy["resolved_status"],
                "resolution": payload.resolution,
                "reason": payload.reason,
                "resolved_by": user.id,
                "resolved_at": timestamp,
                "updated_at": timestamp,
            },
        )
        if not updated:
            raise HTTPException(
                status_code=409, detail={"code": policy["already_resolved_code"]}
            )
        await audit(
            user.id,
            "collaboration_conflict_resolved",
            "DraftConflict",
            conflict_id,
            project_id,
            {"resolution": payload.resolution, "reason": payload.reason},
        )
        return {"conflict": updated, "result": result}
