from itertools import product
from math import prod

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.repositories.execution_asset import execution_asset_repository
from src.services.domain_policy import domain_policy


DATA_SET_POLICY = domain_policy("data_set")


def public_version(version):
    if not version:
        return None
    return {
        **version,
        "variable_names": sorted((version.get("variables") or {}).keys()),
        "secret_names": sorted((version.get("secret_refs") or {}).keys()),
        "secret_refs": {
            key: DATA_SET_POLICY["secret_mask"]
            for key in sorted((version.get("secret_refs") or {}).keys())
        },
    }


def expand_variables(variables, max_rows):
    keys = sorted(variables)
    choices = []
    for key in keys:
        value = variables[key]
        values = value if isinstance(value, list) else [value]
        choices.append(values[:max_rows])
    total = prod(len(values) for values in choices) if choices else 1
    rows = []
    combinations = product(*choices) if choices else [()]
    for combination in combinations:
        rows.append(dict(zip(keys, combination)))
        if len(rows) >= max_rows:
            break
    return rows, total > max_rows


class DataSetService:
    @staticmethod
    async def _get_version(data_set_id, version_id, user, permission=None):
        data_set = await get_project_entity(
            DATA_SET_POLICY["collection"],
            data_set_id,
            user,
            permission or DATA_SET_POLICY["read_permission"],
        )
        version = await execution_asset_repository.find_data_set_version(
            data_set["project_id"], data_set_id, version_id
        )
        if not version:
            raise HTTPException(status_code=404, detail={"code": DATA_SET_POLICY["version_not_found_code"]})
        return data_set, version

    @staticmethod
    async def create(project_id, payload, user):
        await get_project(project_id, user, DATA_SET_POLICY["create_permission"])
        timestamp = now()
        data_set_id = new_id(DATA_SET_POLICY["id_prefix"])
        version = {
            "_id": new_id(DATA_SET_POLICY["version_id_prefix"]),
            "project_id": project_id,
            "data_set_id": data_set_id,
            "version": DATA_SET_POLICY["initial_version"],
            **payload.model_dump(),
            "change_reason": DATA_SET_POLICY["initial_change_reason"],
            "created_by": user.id,
            "created_at": timestamp,
        }
        data_set = {
            "_id": data_set_id,
            "project_id": project_id,
            "name": payload.name,
            "current_version_id": version["_id"],
            "revision": DATA_SET_POLICY["initial_revision"],
            "status": DATA_SET_POLICY["active_status"],
            "created_by": user.id,
            "created_at": timestamp,
            "updated_at": timestamp,
        }
        try:
            await execution_asset_repository.create_data_set(data_set, version)
        except DuplicateKeyError:
            raise HTTPException(status_code=409, detail={"code": DATA_SET_POLICY["name_exists_code"]})
        await audit(user.id, DATA_SET_POLICY["created_event"], DATA_SET_POLICY["entity"], data_set_id, project_id)
        return {**data_set, "current_version": public_version(version)}

    @staticmethod
    async def list(project_id, query_text, limit, user):
        await get_project(project_id, user, DATA_SET_POLICY["read_permission"])
        query = {"project_id": project_id, "status": DATA_SET_POLICY["active_status"]}
        if query_text:
            query["name"] = {"$regex": query_text, "$options": "i"}
        items = await execution_asset_repository.list_data_sets(query, limit)
        version_ids = [item["current_version_id"] for item in items]
        versions = await execution_asset_repository.list_data_set_versions(
            {"project_id": project_id, "_id": {"$in": version_ids}}, limit
        )
        by_id = {item["_id"]: item for item in versions}
        return [
            {**item, "current_version": public_version(by_id.get(item["current_version_id"]))}
            for item in items
        ]

    @staticmethod
    async def get(data_set_id, user):
        data_set = await get_project_entity(DATA_SET_POLICY["collection"], data_set_id, user, DATA_SET_POLICY["read_permission"])
        version = await execution_asset_repository.find_data_set_version(
            data_set["project_id"], data_set_id, data_set["current_version_id"]
        )
        return {**data_set, "current_version": public_version(version)}

    @staticmethod
    async def list_versions(data_set_id, user):
        data_set = await get_project_entity(DATA_SET_POLICY["collection"], data_set_id, user, DATA_SET_POLICY["read_permission"])
        versions = await execution_asset_repository.list_data_set_versions(
            {"project_id": data_set["project_id"], "data_set_id": data_set_id},
            DATA_SET_POLICY["version_limit"],
            newest_first=True,
        )
        return [public_version(version) for version in versions]

    @staticmethod
    async def create_version(data_set_id, payload, user):
        data_set = await get_project_entity(DATA_SET_POLICY["collection"], data_set_id, user, DATA_SET_POLICY["update_permission"])
        if data_set.get("current_version_id") != payload.expected_current_version_id:
            raise HTTPException(
                status_code=409,
                detail={"code": DATA_SET_POLICY["revision_conflict_code"], "current_version_id": data_set.get("current_version_id")},
            )
        current = await execution_asset_repository.find_data_set_version(
            data_set["project_id"], data_set_id, payload.expected_current_version_id
        )
        if not current:
            raise HTTPException(status_code=409, detail={"code": DATA_SET_POLICY["history_invalid_code"]})
        timestamp = now()
        version = {
            "_id": new_id(DATA_SET_POLICY["version_id_prefix"]),
            "project_id": data_set["project_id"],
            "data_set_id": data_set_id,
            "version": int(current["version"]) + 1,
            "name": payload.name,
            "variables": payload.variables,
            "secret_refs": payload.secret_refs,
            "change_reason": payload.change_reason,
            "parent_version_id": current["_id"],
            "created_by": user.id,
            "created_at": timestamp,
        }
        try:
            created = await execution_asset_repository.create_data_set_version(
                data_set, version, payload.name, timestamp
            )
        except DuplicateKeyError as error:
            raise HTTPException(status_code=409, detail={"code": DATA_SET_POLICY["version_conflict_code"]}) from error
        if not created:
            raise HTTPException(status_code=409, detail={"code": DATA_SET_POLICY["revision_conflict_code"]})
        await audit(
            user.id,
            DATA_SET_POLICY["version_created_event"],
            DATA_SET_POLICY["version_entity"],
            version["_id"],
            data_set["project_id"],
            {"data_set_id": data_set_id, "version": version["version"]},
        )
        return public_version(version), data_set["revision"] + 1

    @classmethod
    async def bind(cls, project_id, data_set_id, payload, user):
        data_set, version = await cls._get_version(
            data_set_id, payload.data_set_version_id, user, DATA_SET_POLICY["bind_permission"]
        )
        if data_set["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": DATA_SET_POLICY["project_mismatch_code"]})
        draft = await get_project_entity(DATA_SET_POLICY["draft_collection"], payload.test_case_draft_id, user, DATA_SET_POLICY["bind_permission"])
        if draft["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": DATA_SET_POLICY["project_mismatch_code"]})
        if draft.get("status") != DATA_SET_POLICY["draft_status"]:
            raise HTTPException(status_code=409, detail={"code": DATA_SET_POLICY["draft_immutable_code"]})
        updated = await execution_asset_repository.bind_data_set_version(
            draft["_id"],
            project_id,
            payload.expected_revision,
            version["_id"],
            DATA_SET_POLICY["draft_status"],
            now(),
        )
        if not updated:
            raise HTTPException(status_code=409, detail={"code": DATA_SET_POLICY["revision_conflict_code"]})
        await audit(
            user.id,
            DATA_SET_POLICY["bound_event"],
            DATA_SET_POLICY["version_entity"],
            version["_id"],
            project_id,
            {"test_case_draft_id": draft["_id"]},
        )
        return updated

    @classmethod
    async def preview(cls, project_id, data_set_id, payload, user):
        data_set, version = await cls._get_version(data_set_id, payload.data_set_version_id, user)
        if data_set["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": DATA_SET_POLICY["project_mismatch_code"]})
        rows, truncated = expand_variables(version.get("variables") or {}, payload.max_rows)
        return {
            "data_set_id": data_set_id,
            "data_set_version_id": version["_id"],
            "items": rows,
            "secret_names": sorted((version.get("secret_refs") or {}).keys()),
            "truncated": truncated,
        }

    @staticmethod
    async def archive(project_id, data_set_id, payload, user):
        data_set = await get_project_entity(DATA_SET_POLICY["collection"], data_set_id, user, DATA_SET_POLICY["archive_permission"])
        if data_set["project_id"] != project_id:
            raise HTTPException(status_code=422, detail={"code": DATA_SET_POLICY["project_mismatch_code"]})
        if data_set.get("status") == DATA_SET_POLICY["archived_status"]:
            return data_set
        updated = await execution_asset_repository.archive_data_set(
            data_set_id,
            project_id,
            payload.expected_revision,
            payload.reason,
            DATA_SET_POLICY["active_status"],
            DATA_SET_POLICY["archived_status"],
            now(),
        )
        if not updated:
            raise HTTPException(status_code=409, detail={"code": DATA_SET_POLICY["revision_conflict_code"]})
        await audit(user.id, DATA_SET_POLICY["archived_event"], DATA_SET_POLICY["entity"], data_set_id, project_id, {"reason": payload.reason})
        return updated
