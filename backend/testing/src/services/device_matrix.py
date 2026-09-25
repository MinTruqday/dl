from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser
from src.core.common import audit, get_project, get_project_entity, new_id, now, optimistic_patch
from src.repositories import test_design_repository
from src.domain.contracts import (
    DeviceMatrixArchive,
    DeviceMatrixAssignment,
    DeviceMatrixCreate,
    DeviceMatrixPatch,
)
from src.services.domain_policy import domain_policy


DEVICE_POLICY = domain_policy("device_matrix")


class DeviceMatrixService:
    @staticmethod
    async def list(project_id: str, include_archived: bool, user: CurrentUser):
        await get_project(project_id, user, DEVICE_POLICY["read_permission"])
        query = {"project_id": project_id}
        if not include_archived:
            query["status"] = {"$ne": DEVICE_POLICY["archived_status"]}
        return await test_design_repository.list_device_matrices(query)

    @staticmethod
    async def get(matrix_id: str, user: CurrentUser):
        return await get_project_entity(
            DEVICE_POLICY["collection"], matrix_id, user, DEVICE_POLICY["read_permission"]
        )

    @staticmethod
    async def create(project_id: str, payload: DeviceMatrixCreate, user: CurrentUser):
        await get_project(project_id, user, DEVICE_POLICY["manage_permission"])
        timestamp = now()
        matrix = {
            "_id": new_id(DEVICE_POLICY["id_prefix"]),
            "project_id": project_id,
            **payload.model_dump(),
            "status": DEVICE_POLICY["active_status"],
            "revision": DEVICE_POLICY["initial_revision"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await test_design_repository.insert_device_matrix(matrix)
        except DuplicateKeyError as error:
            raise HTTPException(
                status_code=409, detail={"code": DEVICE_POLICY["name_exists_code"]}
            ) from error
        await audit(
            user.id,
            DEVICE_POLICY["created_event"],
            DEVICE_POLICY["entity"],
            matrix["_id"],
            project_id,
        )
        return matrix

    @staticmethod
    async def update(matrix_id: str, payload: DeviceMatrixPatch, user: CurrentUser):
        matrix = await get_project_entity(
            DEVICE_POLICY["collection"], matrix_id, user, DEVICE_POLICY["manage_permission"]
        )
        if matrix.get("status") != DEVICE_POLICY["active_status"]:
            raise HTTPException(
                status_code=409, detail={"code": DEVICE_POLICY["archived_code"]}
            )
        try:
            updated = await optimistic_patch(
                DEVICE_POLICY["collection"],
                matrix_id,
                matrix["project_id"],
                payload.expected_revision,
                payload.model_dump(exclude_unset=True),
            )
        except DuplicateKeyError as error:
            raise HTTPException(
                status_code=409, detail={"code": DEVICE_POLICY["name_exists_code"]}
            ) from error
        await audit(
            user.id,
            DEVICE_POLICY["updated_event"],
            DEVICE_POLICY["entity"],
            matrix_id,
            matrix["project_id"],
        )
        return updated

    @staticmethod
    async def archive(matrix_id: str, payload: DeviceMatrixArchive, user: CurrentUser):
        matrix = await get_project_entity(
            DEVICE_POLICY["collection"], matrix_id, user, DEVICE_POLICY["manage_permission"]
        )
        if matrix.get("status") == DEVICE_POLICY["archived_status"]:
            return matrix
        updated = await optimistic_patch(
            DEVICE_POLICY["collection"],
            matrix_id,
            matrix["project_id"],
            payload.expected_revision,
            {
                "status": DEVICE_POLICY["archived_status"],
                "archive_reason": payload.reason,
                "archived_by": user.id,
                "archived_at": now(),
            },
        )
        await audit(
            user.id,
            DEVICE_POLICY["archived_event"],
            DEVICE_POLICY["entity"],
            matrix_id,
            matrix["project_id"],
            {"reason": payload.reason},
        )
        return updated

    @staticmethod
    async def assign(matrix_id: str, payload: DeviceMatrixAssignment, user: CurrentUser):
        matrix = await get_project_entity(
            DEVICE_POLICY["collection"], matrix_id, user, DEVICE_POLICY["assign_permission"]
        )
        if matrix.get("status") != DEVICE_POLICY["active_status"]:
            raise HTTPException(
                status_code=409, detail={"code": DEVICE_POLICY["archived_code"]}
            )
        enabled_profiles = {
            item["key"]: item for item in matrix.get("profiles", []) if item.get("enabled", True)
        }
        selected_keys = list(dict.fromkeys(payload.profile_keys or enabled_profiles.keys()))
        if not selected_keys or not set(selected_keys) <= set(enabled_profiles):
            raise HTTPException(
                status_code=422, detail={"code": DEVICE_POLICY["selection_invalid_code"]}
            )
        collection = (
            DEVICE_POLICY["test_plan_collection"]
            if payload.target_type == "test_plan"
            else DEVICE_POLICY["test_run_collection"]
        )
        target = await get_project_entity(
            collection, payload.target_id, user, "device_matrix.assign"
        )
        if target["project_id"] != matrix["project_id"]:
            raise HTTPException(
                status_code=422, detail={"code": DEVICE_POLICY["project_mismatch_code"]}
            )
        if target.get("status") != DEVICE_POLICY["draft_status"]:
            raise HTTPException(
                status_code=409, detail={"code": DEVICE_POLICY["target_frozen_code"]}
            )
        snapshot = {
            "matrix_id": matrix_id,
            "matrix_name": matrix["name"],
            "matrix_revision": matrix["revision"],
            "profile_keys": selected_keys,
            "profiles": [enabled_profiles[key] for key in selected_keys],
            "captured_at": now(),
        }
        updated = await optimistic_patch(
            collection,
            payload.target_id,
            matrix["project_id"],
            payload.expected_target_revision,
            {
                "device_matrix_id": matrix_id,
                "device_profile_keys": selected_keys,
                "device_matrix_snapshot": snapshot,
            },
        )
        await audit(
            user.id,
            DEVICE_POLICY["assigned_event"],
            DEVICE_POLICY["test_plan_entity"]
            if payload.target_type == "test_plan"
            else DEVICE_POLICY["test_run_entity"],
            payload.target_id,
            matrix["project_id"],
            {
                "device_matrix_id": matrix_id,
                "matrix_revision": matrix["revision"],
                "profile_keys": selected_keys,
            },
        )
        return updated
