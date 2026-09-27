from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.repositories.project_connector import project_connector_repository





def public_connector(value):
    result = dict(value)
    result["connector_reference"] = 'Đã cấu hình'
    return result


class ProjectConnectorService:
    @staticmethod
    async def list(project_id, user):
        await get_project(project_id, user, 'project.connector.read')
        items = await project_connector_repository.list_connectors(project_id)
        return [public_connector(item) for item in items]

    @staticmethod
    async def bind(project_id, payload, user):
        await get_project(project_id, user, 'project.connector.manage')
        timestamp = now()
        value = {
            "_id": new_id('CONN'),
            "project_id": project_id,
            "provider": payload.provider,
            "connector_reference": payload.connector_reference,
            "external_target": payload.external_target,
            "field_mapping": payload.field_mapping,
            "mapping_version": 1,
            "mapping_versions": [
                {
                    "version": 1,
                    "field_mapping": payload.field_mapping,
                    "created_by": user.id,
                    "created_at": timestamp,
                }
            ],
            "status": 'BOUND',
            "enabled": True,
            "last_cursor": None,
            "last_sync_status": 'NEVER',
            "revision": 1,
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await project_connector_repository.insert_connector(value)
        except DuplicateKeyError:
            raise HTTPException(
                status_code=409,
                detail={"code": 'CONNECTOR_ALREADY_BOUND'},
            )
        await audit(
            user.id,
            'project_connector_bound',
            'ProjectConnector',
            value["_id"],
            project_id,
            {"provider": payload.provider, "external_target": payload.external_target},
        )
        return public_connector(value)

    @staticmethod
    async def update(project_id, connector_id, payload, user):
        connector = await get_project_entity(
            'project_connectors',
            connector_id,
            user,
            'project.connector.manage',
        )
        if connector["project_id"] != project_id:
            raise HTTPException(
                status_code=422,
                detail={"code": 'PROJECT_MISMATCH'},
            )
        changes = payload.model_dump(exclude_unset=True)
        changes.pop("expected_revision", None)
        changes.pop("confirm_external_target", None)
        if payload.field_mapping is not None:
            mapping_version = connector.get(
                "mapping_version", 1
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
                detail={"code": 'REVISION_CONFLICT'},
            )
        await audit(
            user.id,
            'project_connector_updated',
            'ProjectConnector',
            connector_id,
            project_id,
            {"mapping_version": updated.get("mapping_version")},
        )
        return public_connector(updated)

    @staticmethod
    async def unbind(project_id, connector_id, payload, user):
        connector = await get_project_entity(
            'project_connectors',
            connector_id,
            user,
            'project.connector.manage',
        )
        if connector["project_id"] != project_id:
            raise HTTPException(
                status_code=422,
                detail={"code": 'PROJECT_MISMATCH'},
            )
        if not payload.confirm_external_target:
            raise HTTPException(
                status_code=422,
                detail={"code": 'TARGET_CONFIRMATION_REQUIRED'},
            )
        timestamp = now()
        updated = await project_connector_repository.unbind_connector(
            connector_id,
            project_id,
            payload.expected_revision,
            'BOUND',
            {
                "status": 'UNBOUND',
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
                detail={"code": 'CONNECTOR_STATE_CONFLICT'},
            )
        await audit(
            user.id,
            'project_connector_unbound',
            'ProjectConnector',
            connector_id,
            project_id,
            {"external_target": connector["external_target"], "reason": payload.reason},
        )
        return public_connector(updated)

    @staticmethod
    async def start_sync(project_id, connector_id, payload, user):
        connector = await get_project_entity(
            'project_connectors',
            connector_id,
            user,
            'project.connector.sync',
        )
        if connector["project_id"] != project_id:
            raise HTTPException(
                status_code=422,
                detail={"code": 'PROJECT_MISMATCH'},
            )
        if connector.get("status") != 'BOUND' or not connector.get(
            "enabled"
        ):
            raise HTTPException(
                status_code=409,
                detail={"code": 'CONNECTOR_NOT_ACTIVE'},
            )
        existing = await project_connector_repository.find_job_by_idempotency_key(
            project_id, payload.idempotency_key
        )
        if existing:
            if existing.get("connector_id") != connector_id:
                raise HTTPException(
                    status_code=409,
                    detail={"code": 'IDEMPOTENCY_KEY_REUSED'},
                )
            return existing
        timestamp = now()
        value = {
            "_id": new_id('SYNC'),
            "project_id": project_id,
            "connector_id": connector_id,
            "direction": payload.direction,
            "scopes": payload.scopes,
            "cursor_before": connector.get("last_cursor"),
            "status": 'QUEUED',
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
            'connector_sync_queued',
            'SyncCursor',
            value["_id"],
            project_id,
            {"direction": payload.direction, "scopes": payload.scopes},
        )
        return value

    @staticmethod
    async def list_sync_log(project_id, user):
        await get_project(project_id, user, 'project.connector.read')
        items = await project_connector_repository.list_jobs(project_id)
        for item in items:
            item.pop("raw_payload", None)
            item.pop("secret", None)
        return items

    @staticmethod
    async def list_conflicts(project_id, user):
        await get_project(project_id, user, 'project.connector.review')
        return await project_connector_repository.list_conflicts(project_id)

    @staticmethod
    async def resolve_conflict(project_id, conflict_id, payload, user):
        conflict = await get_project_entity(
            'connector_sync_conflicts',
            conflict_id,
            user,
            'project.connector.review',
        )
        if conflict["project_id"] != project_id:
            raise HTTPException(
                status_code=422,
                detail={"code": 'PROJECT_MISMATCH'},
            )
        timestamp = now()
        updated = await project_connector_repository.resolve_conflict(
            conflict_id,
            project_id,
            payload.expected_revision,
            'OPEN',
            {
                "status": 'RESOLVED',
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
                detail={"code": 'CONFLICT_ALREADY_RESOLVED'},
            )
        await audit(
            user.id,
            'connector_conflict_resolved',
            'SyncConflict',
            conflict_id,
            project_id,
            {"resolution": payload.resolution, "reason": payload.reason},
        )
        return updated
