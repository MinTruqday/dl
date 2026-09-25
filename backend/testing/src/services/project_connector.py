from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.repositories import project_connector_repository
from src.services.domain_policy import domain_policy


CONNECTOR_POLICY = domain_policy("project_connector")


def public_connector(value):
    result = dict(value)
    result["connector_reference"] = CONNECTOR_POLICY["configured_label"]
    return result


class ProjectConnectorService:
    @staticmethod
    async def list(project_id, user):
        await get_project(project_id, user, CONNECTOR_POLICY["read_permission"])
        items = await project_connector_repository.list_connectors(project_id)
        return [public_connector(item) for item in items]

    @staticmethod
    async def bind(project_id, payload, user):
        await get_project(project_id, user, CONNECTOR_POLICY["manage_permission"])
        timestamp = now()
        value = {
            "_id": new_id(CONNECTOR_POLICY["connector_id_prefix"]),
            "project_id": project_id,
            "provider": payload.provider,
            "connector_reference": payload.connector_reference,
            "external_target": payload.external_target,
            "field_mapping": payload.field_mapping,
            "mapping_version": CONNECTOR_POLICY["initial_mapping_version"],
            "mapping_versions": [
                {
                    "version": CONNECTOR_POLICY["initial_mapping_version"],
                    "field_mapping": payload.field_mapping,
                    "created_by": user.id,
                    "created_at": timestamp,
                }
            ],
            "status": CONNECTOR_POLICY["bound_status"],
            "enabled": True,
            "last_cursor": None,
            "last_sync_status": CONNECTOR_POLICY["never_synced_status"],
            "revision": CONNECTOR_POLICY["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await project_connector_repository.insert_connector(value)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=409,
                detail={"code": CONNECTOR_POLICY["already_bound_code"]},
            )
        await audit(
            user.id,
            CONNECTOR_POLICY["bound_event"],
            CONNECTOR_POLICY["connector_entity"],
            value["_id"],
            project_id,
            {"provider": payload.provider, "external_target": payload.external_target},
        )
        return public_connector(value)

    @staticmethod
    async def update(project_id, connector_id, payload, user):
        connector = await get_project_entity(
            CONNECTOR_POLICY["connector_collection"],
            connector_id,
            user,
            CONNECTOR_POLICY["manage_permission"],
        )
        if connector["project_id"] != project_id:
            raise HTTPException(
                status_code=422,
                detail={"code": CONNECTOR_POLICY["project_mismatch_code"]},
            )
        changes = payload.model_dump(exclude_unset=True)
        changes.pop("expected_revision", None)
        changes.pop("confirm_external_target", None)
        if payload.field_mapping is not None:
            mapping_version = connector.get(
                "mapping_version", CONNECTOR_POLICY["initial_mapping_version"]
            ) + 1
            changes["mapping_version"] = mapping_version
            changes["mapping_versions"] = [
                *connector.get("mapping_versions", []),
                {
                    "version": mapping_version,
                    "field_mapping": payload.field_mapping,
                    "created_by": user.id,
                    "created_at": now(),
                },
            ]
        updated = await project_connector_repository.update_connector(
            connector_id,
            project_id,
            payload.expected_revision,
            {**changes, "updated_at": now()},
        )
        if not updated:
            raise HTTPException(
                status_code=409,
                detail={"code": CONNECTOR_POLICY["revision_conflict_code"]},
            )
        await audit(
            user.id,
            CONNECTOR_POLICY["updated_event"],
            CONNECTOR_POLICY["connector_entity"],
            connector_id,
            project_id,
            {"mapping_version": updated.get("mapping_version")},
        )
        return public_connector(updated)

    @staticmethod
    async def unbind(project_id, connector_id, payload, user):
        connector = await get_project_entity(
            CONNECTOR_POLICY["connector_collection"],
            connector_id,
            user,
            CONNECTOR_POLICY["manage_permission"],
        )
        if connector["project_id"] != project_id:
            raise HTTPException(
                status_code=422,
                detail={"code": CONNECTOR_POLICY["project_mismatch_code"]},
            )
        if not payload.confirm_external_target:
            raise HTTPException(
                status_code=422,
                detail={"code": CONNECTOR_POLICY["target_confirmation_code"]},
            )
        timestamp = now()
        updated = await project_connector_repository.unbind_connector(
            connector_id,
            project_id,
            payload.expected_revision,
            {
                "status": CONNECTOR_POLICY["unbound_status"],
                "enabled": False,
                "unbind_reason": payload.reason,
                "unbound_by": user.id,
                "unbound_at": timestamp,
                "updated_at": timestamp,
            },
        )
        if not updated:
            raise HTTPException(
                status_code=409,
                detail={"code": CONNECTOR_POLICY["state_conflict_code"]},
            )
        await audit(
            user.id,
            CONNECTOR_POLICY["unbound_event"],
            CONNECTOR_POLICY["connector_entity"],
            connector_id,
            project_id,
            {"external_target": connector["external_target"], "reason": payload.reason},
        )
        return public_connector(updated)

    @staticmethod
    async def start_sync(project_id, connector_id, payload, user):
        connector = await get_project_entity(
            CONNECTOR_POLICY["connector_collection"],
            connector_id,
            user,
            CONNECTOR_POLICY["sync_permission"],
        )
        if connector["project_id"] != project_id:
            raise HTTPException(
                status_code=422,
                detail={"code": CONNECTOR_POLICY["project_mismatch_code"]},
            )
        if connector.get("status") != CONNECTOR_POLICY["bound_status"] or not connector.get(
            "enabled"
        ):
            raise HTTPException(
                status_code=409,
                detail={"code": CONNECTOR_POLICY["not_active_code"]},
            )
        existing = await project_connector_repository.find_job_by_idempotency_key(
            project_id, payload.idempotency_key
        )
        if existing:
            if existing.get("connector_id") != connector_id:
                raise HTTPException(
                    status_code=409,
                    detail={"code": CONNECTOR_POLICY["idempotency_reused_code"]},
                )
            return existing
        timestamp = now()
        value = {
            "_id": new_id(CONNECTOR_POLICY["sync_id_prefix"]),
            "project_id": project_id,
            "connector_id": connector_id,
            "direction": payload.direction,
            "scopes": payload.scopes,
            "cursor_before": connector.get("last_cursor"),
            "status": CONNECTOR_POLICY["queued_status"],
            "conflict_aware": True,
            "idempotency_key": payload.idempotency_key,
            "requested_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await project_connector_repository.insert_job(value)
        except DuplicateKeyError:
            existing = await project_connector_repository.find_job_by_idempotency_key(
                project_id, payload.idempotency_key
            )
            if existing:
                return existing
            raise
        await audit(
            user.id,
            CONNECTOR_POLICY["sync_queued_event"],
            CONNECTOR_POLICY["sync_entity"],
            value["_id"],
            project_id,
            {"direction": payload.direction, "scopes": payload.scopes},
        )
        return value

    @staticmethod
    async def list_sync_log(project_id, user):
        await get_project(project_id, user, CONNECTOR_POLICY["read_permission"])
        items = await project_connector_repository.list_jobs(project_id)
        for item in items:
            item.pop("raw_payload", None)
            item.pop("secret", None)
        return items

    @staticmethod
    async def list_conflicts(project_id, user):
        await get_project(project_id, user, CONNECTOR_POLICY["review_permission"])
        return await project_connector_repository.list_conflicts(project_id)

    @staticmethod
    async def resolve_conflict(project_id, conflict_id, payload, user):
        conflict = await get_project_entity(
            CONNECTOR_POLICY["conflict_collection"],
            conflict_id,
            user,
            CONNECTOR_POLICY["review_permission"],
        )
        if conflict["project_id"] != project_id:
            raise HTTPException(
                status_code=422,
                detail={"code": CONNECTOR_POLICY["project_mismatch_code"]},
            )
        timestamp = now()
        updated = await project_connector_repository.resolve_conflict(
            conflict_id,
            project_id,
            payload.expected_revision,
            {
                "status": CONNECTOR_POLICY["resolved_status"],
                "resolution": payload.resolution,
                "merged_value": payload.merged_value,
                "reason": payload.reason,
                "resolved_by": user.id,
                "resolved_at": timestamp,
                "updated_at": timestamp,
            },
        )
        if not updated:
            raise HTTPException(
                status_code=409,
                detail={"code": CONNECTOR_POLICY["conflict_resolved_code"]},
            )
        await audit(
            user.id,
            CONNECTOR_POLICY["conflict_resolved_event"],
            CONNECTOR_POLICY["conflict_entity"],
            conflict_id,
            project_id,
            {"resolution": payload.resolution, "reason": payload.reason},
        )
        return updated
