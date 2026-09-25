from datetime import datetime, timezone
from math import ceil
from uuid import uuid4

from fastapi import HTTPException

from src.clients.authentication import load_accounts, resolve_account
from src.core.auth import (
    ARCHIVE_READ_PERMISSIONS,
    PROJECT_PERMISSIONS,
    CurrentUser,
    permissions_for_role,
)
from src.repositories import common_repository
from src.services.domain_policy import domain_policy

CORE_POLICY = domain_policy("core")
RETRYABLE_ERROR_CODES = frozenset(CORE_POLICY["retryable_error_codes"])
VIEWER_DEFECT_FIELDS = frozenset(CORE_POLICY["viewer"]["defect_fields"])


def new_id(prefix: str):
    return f"{prefix}-{uuid4().hex}"


def now():
    return datetime.now(timezone.utc)


async def get_project_role(project_id, user_id):
    access = CORE_POLICY["project_access"]
    membership = await common_repository.find_membership(
        project_id,
        user_id,
        status=access["active_membership_status"],
        projection={"project_role": 1},
    )
    return (membership or {}).get("project_role")


def visible_defect(defect, role):
    if role != CORE_POLICY["viewer"]["role"]:
        return defect
    return {key: value for key, value in defect.items() if key in VIEWER_DEFECT_FIELDS}


async def load_user_identities(user_ids):
    identifiers = sorted({str(value) for value in user_ids if value})
    return await load_accounts(identifiers)


async def resolve_user_reference(value):
    reference = str(value or "").strip()
    if not reference:
        return reference
    return await resolve_account(reference)


def envelope(
    data=None,
    revision=None,
    trace_id=None,
    operation_id=None,
    status=CORE_POLICY["response"]["success_status"],
    error_code=None,
    retryable=False,
    state_after_failure=None,
    user_action_required=False,
    degraded_mode=None,
):
    meta = {"trace_id": trace_id or new_id(CORE_POLICY["response"]["trace_id_prefix"])}
    if revision is not None:
        meta["revision"] = revision
    if operation_id is not None:
        meta["operation_id"] = operation_id
    operation = {
        "status": status,
        "error_code": error_code,
        "retryable": retryable,
        "state_after_failure": state_after_failure,
        "user_action_required": user_action_required,
    }
    if degraded_mode:
        operation["degraded_mode"] = degraded_mode
    meta["operation"] = operation
    return {"data": data, "meta": meta, **operation}


def page_payload(items, page, page_size, total):
    return {
        "items": items,
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": ceil(total / page_size) if total else 0,
    }


def sort_spec(value, allowed, default="-updated_at"):
    selected = value or default
    descending = selected.startswith("-")
    field = selected[1:] if descending else selected
    if field not in allowed:
        raise HTTPException(
            status_code=422,
            detail={
                "code": CORE_POLICY["project_access"]["error_codes"]["invalid_sort_field"],
                "allowed": sorted(allowed),
            },
        )
    return field, -1 if descending else 1


def failure_metadata(code, status_code=500, detail=None):
    detail = detail if isinstance(detail, dict) else {}
    retryable = detail.get(
        "retryable",
        code in RETRYABLE_ERROR_CODES
        or status_code in CORE_POLICY["response"]["retryable_http_statuses"],
    )
    state_after_failure = detail.get("state_after_failure") or (
        CORE_POLICY["response"]["unchanged_failure_state"]
        if status_code < 500
        else CORE_POLICY["response"]["retryable_failure_state"]
    )
    user_action_required = detail.get(
        "user_action_required", status_code in {409, 422, 403} or not retryable
    )
    return {
        "status": CORE_POLICY["response"]["failed_status"],
        "error_code": code,
        "retryable": retryable,
        "state_after_failure": state_after_failure,
        "user_action_required": user_action_required,
    }


async def audit(
    user_id: str,
    action: str,
    entity_type: str,
    entity_id: str,
    project_id: str | None,
    details: dict | None = None,
):
    event = {
        "_id": new_id(CORE_POLICY["response"]["audit_id_prefix"]),
        "project_id": project_id,
        "actor_id": user_id,
        "action": action,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "details": details or {},
        "created_at": now(),
    }
    return await common_repository.insert_audit_event(event)


async def get_project(
    project_id: str,
    user: CurrentUser,
    permission: str = CORE_POLICY["project_access"]["default_permission"],
    assigned_role: str | None = None,
    assigned_user_id: str | None = None,
):
    access = CORE_POLICY["project_access"]
    codes = access["error_codes"]
    project = await common_repository.find_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail={"code": codes["entity_not_found"]})
    membership = await common_repository.find_membership(project_id, user.id)
    grant = await common_repository.find_active_grant(
        project_id, user.id, access["active_membership_status"], now()
    )
    grant_permissions = set(grant.get("permissions", [])) & PROJECT_PERMISSIONS if grant else set()
    if not membership and permission not in grant_permissions:
        await audit(
            user.id,
            access["audit_actions"]["membership_required"],
            access["project_entity_type"],
            project_id,
            project_id,
            {"permission": permission, "system_role": user.system_role.value},
        )
        raise HTTPException(status_code=403, detail={"code": codes["membership_required"]})
    if membership and membership.get("status") != access["active_membership_status"] and permission not in grant_permissions:
        raise HTTPException(status_code=403, detail={"code": codes["membership_inactive"]})
    if project.get("administrative_status", access["active_administrative_status"]) != access["active_administrative_status"]:
        raise HTTPException(status_code=423, detail={"code": codes["administratively_suspended"]})
    permissions = (
        permissions_for_role(membership.get("project_role", ""), project.get("settings"))
        if membership and membership.get("status") == access["active_membership_status"]
        else set()
    )
    assigned_access = (
        assigned_role is not None
        and membership is not None
        and membership.get("project_role") == assigned_role
        and assigned_user_id == user.id
    )
    if (
        permission not in permissions
        and permission not in grant_permissions
        and not assigned_access
    ):
        await audit(
            user.id,
            access["audit_actions"]["permission_denied"],
            access["project_entity_type"],
            project_id,
            project_id,
            {
                "permission": permission,
                "project_role": membership.get("project_role") if membership else None,
            },
        )
        raise HTTPException(
            status_code=403, detail={"code": codes["permission_denied"], "permission": permission}
        )
    if (
        project.get("status", access["default_project_status"]).lower() == access["archived_project_status"]
        and permission not in ARCHIVE_READ_PERMISSIONS
        and permission != access["restore_permission"]
    ):
        raise HTTPException(status_code=409, detail={"code": codes["archived"]})
    if (
        project.get("status", access["default_project_status"]).lower() == access["archived_project_status"]
        and permission in ARCHIVE_READ_PERMISSIONS
        and permission != access["default_permission"]
        and (project.get("settings") or {}).get("read_after_archive_policy", access["default_archive_read_policy"])
        == access["denied_archive_read_policy"]
    ):
        raise HTTPException(status_code=403, detail={"code": codes["archived_read_denied"]})
    if permission in grant_permissions and permission not in permissions:
        return {
            **project,
            "access_context": {
                "mode": access["break_glass_mode"],
                "grant_id": grant["_id"],
                "permissions": sorted(grant_permissions),
                "expires_at": grant["expires_at"],
                "reason": grant.get("reason"),
            },
        }
    return project


async def require_action_policy(
    project_id: str, user: CurrentUser, action: str, default_roles: set[str]
):
    access = CORE_POLICY["project_access"]
    project = await common_repository.find_project(project_id, {"settings": 1})
    membership = await common_repository.find_membership(
        project_id,
        user.id,
        status=access["active_membership_status"],
        projection={"project_role": 1},
    )
    if not project or not membership:
        raise HTTPException(
            status_code=403, detail={"code": access["error_codes"]["membership_required"]}
        )
    configured = (project.get("settings") or {}).get("action_policies", {}).get(action)
    allowed_roles = set(configured) if isinstance(configured, list) else default_roles
    if membership.get("project_role") not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail={"code": access["error_codes"]["action_policy_denied"], "action": action},
        )
    return project


async def get_project_entity(
    collection: str,
    entity_id: str,
    user: CurrentUser,
    permission: str,
    assigned_role: str | None = None,
    assigned_user_field: str | None = None,
):
    projection = {"_id": 1, "project_id": 1}
    if assigned_user_field:
        projection[assigned_user_field] = 1
    identity = await common_repository.find_entity_identity(
        collection, entity_id, projection
    )
    if not identity:
        raise HTTPException(
            status_code=404,
            detail={"code": CORE_POLICY["project_access"]["error_codes"]["artifact_not_found"]},
        )
    await get_project(
        identity["project_id"],
        user,
        permission,
        assigned_role=assigned_role,
        assigned_user_id=identity.get(assigned_user_field) if assigned_user_field else None,
    )
    entity = await common_repository.find_project_entity(
        collection, entity_id, identity["project_id"]
    )
    if not entity:
        raise HTTPException(
            status_code=404,
            detail={"code": CORE_POLICY["project_access"]["error_codes"]["artifact_not_found"]},
        )
    return entity


async def optimistic_patch(
    collection: str, entity_id: str, project_id: str, expected_revision: int, changes: dict
):
    cleaned = {
        key: value
        for key, value in changes.items()
        if value is not None and key != "expected_revision"
    }
    cleaned["updated_at"] = now()
    entity = await common_repository.optimistic_patch(
        collection,
        entity_id,
        project_id,
        expected_revision,
        cleaned,
        include_project_scope=collection != "projects",
    )
    if entity:
        return entity
    existing = await common_repository.find_entity(collection, entity_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Không tìm thấy dữ liệu")
    raise HTTPException(
        status_code=409,
        detail={
            "code": CORE_POLICY["project_access"]["error_codes"]["revision_conflict"],
            "current_revision": existing.get("revision"),
        },
    )


async def next_key(project_id: str, sequence: str, prefix: str):
    value = await common_repository.next_counter(f"{project_id}:{sequence}")
    return f"{prefix}-{int(value['value']):04d}"


def plain_text(document):
    values = []

    def visit(node):
        if isinstance(node, dict):
            if isinstance(node.get("text"), str):
                values.append(node["text"])
            for child in node.get("content", []):
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(document)
    return " ".join(values).strip()


def validate_doc(value):
    if (
        not isinstance(value, dict)
        or value.get("type") != "doc"
        or not isinstance(value.get("content", []), list)
    ):
        raise HTTPException(status_code=422, detail="Tiptap JSON không hợp lệ")
    return value
