from fastapi import APIRouter, Depends, HTTPException, Query
import os
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, PROJECT_PERMISSIONS, get_current_user, permissions_for_role
from src.core.common import audit, envelope, get_project, new_id, now, optimistic_patch
from src.core.configuration import settings
from src.core.database import database
from src.domain.schemas import (
    ProjectArchiveInput,
    ProjectCreate,
    ProjectMemberCreate,
    ProjectMemberPatch,
    ProjectPatch,
)


router = APIRouter(prefix="/kiem-thu", tags=["Dự án kiểm thử"])


@router.post("/du-an", status_code=201)
async def create_project(payload: ProjectCreate, user: CurrentUser = Depends(get_current_user)):
    policy = settings.PROJECT_CREATION_POLICY
    authentication_db = os.environ.get("AUTHENTICATION_DB_NAME")
    if authentication_db:
        config = await database.client[authentication_db].system_configs.find_one(
            {"type": "project_creation"}
        )
        if config:
            policy = config.get("project_creation_policy", policy)
    if policy == "ADMIN_ONLY" and not user.is_system_admin:
        raise HTTPException(status_code=403, detail={"code": "SYSTEM_PERMISSION_DENIED"})
    timestamp = now()
    project = {
        "_id": new_id("PRJ"),
        **payload.model_dump(),
        "created_by": user.id,
        "status": "active",
        "revision": 1,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    membership = {
        "_id": new_id("PM"),
        "project_id": project["_id"],
        "user_id": user.id,
        "project_role": "QA_LEAD",
        "status": "ACTIVE",
        "membership_revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.projects.insert_one(project)
        try:
            await database.value.project_members.insert_one(membership)
        except Exception:
            await database.value.projects.delete_one({"_id": project["_id"]})
            raise
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "PROJECT_KEY_EXISTS"})
    await audit(
        user.id,
        "project_created",
        "Project",
        project["_id"],
        project["_id"],
        {"creator_membership_id": membership["_id"]},
    )
    return envelope(
        {
            **project,
            "current_membership": membership,
            "current_permissions": sorted(permissions_for_role("QA_LEAD", project["settings"])),
        },
        revision=1,
    )


@router.get("/du-an")
async def list_projects(
    q: str = Query(default="", max_length=200),
    status: str = Query(default="active", max_length=30),
    limit: int = Query(default=50, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
):
    memberships = await database.value.project_members.find(
        {"user_id": user.id, "status": "ACTIVE"}
    ).to_list(5000)
    by_project = {item["project_id"]: item for item in memberships}
    grants = await database.value.break_glass_grants.find(
        {"user_id": user.id, "status": "ACTIVE", "expires_at": {"$gt": now()}}
    ).to_list(5000)
    by_grant = {item["project_id"]: item for item in grants}
    query = {"_id": {"$in": list(set(by_project) | set(by_grant))}}
    if status:
        query["status"] = status
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"key": {"$regex": q, "$options": "i"}},
        ]
    projects = await database.value.projects.find(query).sort("updated_at", -1).to_list(limit)
    items = []
    for project in projects:
        membership = by_project.get(project["_id"])
        grant = by_grant.get(project["_id"])
        role_permissions = (
            permissions_for_role(membership["project_role"], project.get("settings"))
            if membership
            else set()
        )
        grant_permissions = set(grant.get("permissions", [])) & PROJECT_PERMISSIONS if grant else set()
        permissions = role_permissions | grant_permissions
        items.append(
            {
                **project,
                "current_membership": membership,
                "current_permissions": sorted(permissions),
                "access_context": (
                    {
                        "mode": "BREAK_GLASS",
                        "grant_id": grant["_id"],
                        "permissions": sorted(
                            set(grant.get("permissions", [])) & PROJECT_PERMISSIONS
                        ),
                        "expires_at": grant["expires_at"],
                        "reason": grant.get("reason"),
                    }
                    if grant and not grant_permissions.issubset(role_permissions)
                    else None
                ),
            }
        )
    return envelope(items)


@router.get("/du-an/{project_id}")
async def project_detail(project_id: str, user: CurrentUser = Depends(get_current_user)):
    project = await get_project(project_id, user, "project.read")
    membership = await database.value.project_members.find_one(
        {"project_id": project_id, "user_id": user.id, "status": "ACTIVE"}
    )
    grant = await database.value.break_glass_grants.find_one(
        {
            "project_id": project_id,
            "user_id": user.id,
            "status": "ACTIVE",
            "expires_at": {"$gt": now()},
        }
    )
    role_permissions = (
        permissions_for_role(membership["project_role"], project.get("settings"))
        if membership
        else set()
    )
    grant_permissions = set(grant.get("permissions", [])) & PROJECT_PERMISSIONS if grant else set()
    access_context = (
        {
            "mode": "BREAK_GLASS",
            "grant_id": grant["_id"],
            "permissions": sorted(grant_permissions),
            "expires_at": grant["expires_at"],
            "reason": grant.get("reason"),
        }
        if grant and not grant_permissions.issubset(role_permissions)
        else None
    )
    return envelope(
        {
            **project,
            "current_membership": membership,
            "current_permissions": sorted(
                role_permissions | grant_permissions
            ),
            "access_context": access_context,
        }
    )


@router.patch("/du-an/{project_id}")
async def update_project(
    project_id: str, payload: ProjectPatch, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "project.update")
    if payload.settings is not None:
        await get_project(project_id, user, "project.settings.manage")
    updated = await optimistic_patch(
        "projects", project_id, project_id, payload.expected_revision, payload.model_dump()
    )
    await audit(user.id, "project_updated", "Project", project_id, project_id)
    return envelope(updated, revision=updated["revision"])


@router.get(
    "/du-an/{project_id}/cai-dat",
    openapi_extra={"x-function-ids": [f"PSET-{index:02d}" for index in range(1, 13)]},
)
async def read_project_settings(project_id: str, user: CurrentUser = Depends(get_current_user)):
    project = await get_project(project_id, user, "project.settings.manage")
    return envelope(
        {
            "project_id": project_id,
            "name": project.get("name"),
            "description": project.get("description", ""),
            "project_type": project.get("project_type"),
            "locale": project.get("locale"),
            "timezone": project.get("timezone"),
            "settings": project.get("settings", {}),
        },
        revision=project.get("revision", 1),
    )


@router.patch(
    "/du-an/{project_id}/cai-dat",
    openapi_extra={"x-function-ids": [f"PSET-{index:02d}" for index in range(1, 13)]},
)
async def update_project_settings(
    project_id: str, payload: ProjectPatch, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "project.settings.manage")
    changes = payload.model_dump(exclude_none=True)
    changes.pop("expected_revision", None)
    if not changes:
        raise HTTPException(status_code=422, detail={"code": "SETTINGS_EMPTY"})
    updated = await optimistic_patch(
        "projects", project_id, project_id, payload.expected_revision, changes
    )
    await audit(user.id, "project_settings_updated", "ProjectSettings", project_id, project_id)
    return envelope(
        {
            "project_id": project_id,
            "name": updated.get("name"),
            "description": updated.get("description", ""),
            "project_type": updated.get("project_type"),
            "locale": updated.get("locale"),
            "timezone": updated.get("timezone"),
            "settings": updated.get("settings", {}),
        },
        revision=updated["revision"],
    )


@router.post("/du-an/{project_id}/luu-tru")
async def archive_project(
    project_id: str, payload: ProjectArchiveInput, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "project.archive")
    updated = await optimistic_patch(
        "projects",
        project_id,
        project_id,
        payload.expected_revision,
        {
            "status": "archived",
            "archived_by": user.id,
            "archived_at": now(),
            "archive_reason": payload.reason,
        },
    )
    await audit(
        user.id, "project_archived", "Project", project_id, project_id, {"reason": payload.reason}
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/du-an/{project_id}/khoi-phuc")
async def restore_project(
    project_id: str, payload: ProjectArchiveInput, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "project.restore")
    project = await database.value.projects.find_one({"_id": project_id})
    if project.get("status") == "active":
        return envelope(project, revision=project["revision"])
    updated = await optimistic_patch(
        "projects",
        project_id,
        project_id,
        payload.expected_revision,
        {
            "status": "active",
            "restored_by": user.id,
            "restored_at": now(),
            "restore_reason": payload.reason,
        },
    )
    await audit(
        user.id, "project_restored", "Project", project_id, project_id, {"reason": payload.reason}
    )
    return envelope(updated, revision=updated["revision"])


@router.get("/du-an/{project_id}/thanh-vien")
async def list_project_members(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "project.members.read")
    members = (
        await database.value.project_members.find({"project_id": project_id})
        .sort("created_at", 1)
        .to_list(5000)
    )
    return envelope(members)


@router.post("/du-an/{project_id}/thanh-vien", status_code=201)
async def add_project_member(
    project_id: str, payload: ProjectMemberCreate, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "project.members.manage")
    timestamp = now()
    membership = {
        "_id": new_id("PM"),
        "project_id": project_id,
        "user_id": payload.user_id,
        "project_role": payload.project_role,
        "status": "ACTIVE",
        "membership_revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.project_members.insert_one(membership)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "PROJECT_MEMBERSHIP_EXISTS"})
    await audit(
        user.id,
        "project_member_added",
        "ProjectMember",
        membership["_id"],
        project_id,
        {"user_id": payload.user_id, "project_role": payload.project_role},
    )
    return envelope(membership, revision=1)


@router.post("/du-an/{project_id}/loi-moi", status_code=201)
async def invite_project_member(
    project_id: str, payload: ProjectMemberCreate, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "project.members.manage")
    timestamp = now()
    membership = {
        "_id": new_id("PM"),
        "project_id": project_id,
        "user_id": payload.user_id,
        "project_role": payload.project_role,
        "status": "INVITED",
        "membership_revision": 1,
        "invited_by": user.id,
        "invited_at": timestamp,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.project_members.insert_one(membership)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "PROJECT_MEMBERSHIP_EXISTS"})
    await audit(
        user.id,
        "project_member_invited",
        "ProjectMember",
        membership["_id"],
        project_id,
        {"user_id": payload.user_id, "project_role": payload.project_role},
    )
    return envelope(membership, revision=1)


async def _accept_project_invitation(
    invitation_id: str, user: CurrentUser
):
    membership = await database.value.project_members.find_one_and_update(
        {"_id": invitation_id, "user_id": user.id, "status": "INVITED"},
        {
            "$set": {"status": "ACTIVE", "accepted_at": now(), "updated_at": now()},
            "$inc": {"membership_revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not membership:
        raise HTTPException(status_code=404, detail={"code": "INVITATION_NOT_FOUND"})
    project_id = membership["project_id"]
    await audit(
        user.id, "project_invitation_accepted", "ProjectMember", membership["_id"], project_id
    )
    return envelope(membership, revision=membership["membership_revision"])


@router.post(
    "/loi-moi-du-an/{invitation_id}/chap-nhan",
    openapi_extra={"x-function-ids": ["MEM-SELF-01"]},
)
async def accept_project_invitation_by_id(
    invitation_id: str, user: CurrentUser = Depends(get_current_user)
):
    return await _accept_project_invitation(invitation_id, user)


@router.post("/du-an/{project_id}/thanh-vien/{member_user_id}/chap-nhan")
async def accept_project_invitation(
    project_id: str, member_user_id: str, user: CurrentUser = Depends(get_current_user)
):
    if user.id != member_user_id:
        raise HTTPException(status_code=403, detail={"code": "INVITATION_OWNER_REQUIRED"})
    membership = await database.value.project_members.find_one(
        {"project_id": project_id, "user_id": user.id, "status": "INVITED"}, {"_id": 1}
    )
    if not membership:
        raise HTTPException(status_code=404, detail={"code": "INVITATION_NOT_FOUND"})
    return await _accept_project_invitation(membership["_id"], user)


@router.post(
    "/loi-moi-du-an/{invitation_id}/tu-choi",
    openapi_extra={"x-function-ids": ["MEM-SELF-02"]},
)
async def decline_project_invitation(
    invitation_id: str, user: CurrentUser = Depends(get_current_user)
):
    membership = await database.value.project_members.find_one_and_update(
        {"_id": invitation_id, "user_id": user.id, "status": "INVITED"},
        {
            "$set": {"status": "DECLINED", "declined_at": now(), "updated_at": now()},
            "$inc": {"membership_revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not membership:
        raise HTTPException(status_code=404, detail={"code": "INVITATION_NOT_FOUND"})
    await audit(
        user.id,
        "project_invitation_declined",
        "ProjectMember",
        membership["_id"],
        membership["project_id"],
    )
    return envelope(membership, revision=membership["membership_revision"])


@router.post(
    "/du-an/{project_id}/roi-du-an",
    openapi_extra={"x-function-ids": ["MEM-SELF-03"]},
)
async def leave_project(project_id: str, user: CurrentUser = Depends(get_current_user)):
    membership = await database.value.project_members.find_one_and_update(
        {"project_id": project_id, "user_id": user.id, "status": "ACTIVE"},
        {"$set": {"status": "LEFT", "left_at": now(), "updated_at": now()}, "$inc": {"membership_revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not membership:
        raise HTTPException(status_code=404, detail={"code": "PROJECT_MEMBERSHIP_NOT_FOUND"})
    await audit(user.id, "project_member_left", "ProjectMember", membership["_id"], project_id)
    return envelope(membership, revision=membership["membership_revision"])


@router.post("/du-an/{project_id}/thanh-vien/{member_user_id}/gui-lai-loi-moi")
async def resend_project_invitation(
    project_id: str, member_user_id: str, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "project.members.manage")
    membership = await database.value.project_members.find_one_and_update(
        {"project_id": project_id, "user_id": member_user_id, "status": "INVITED"},
        {
            "$set": {"invited_by": user.id, "invited_at": now(), "updated_at": now()},
            "$inc": {"membership_revision": 1, "invite_send_count": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not membership:
        raise HTTPException(status_code=409, detail={"code": "INVITATION_NOT_PENDING"})
    await audit(
        user.id, "project_invitation_resent", "ProjectMember", membership["_id"], project_id
    )
    return envelope(membership, revision=membership["membership_revision"])


@router.post("/du-an/{project_id}/thanh-vien/{member_user_id}/huy-loi-moi")
async def cancel_project_invitation(
    project_id: str, member_user_id: str, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "project.members.manage")
    membership = await database.value.project_members.find_one_and_update(
        {"project_id": project_id, "user_id": member_user_id, "status": "INVITED"},
        {
            "$set": {
                "status": "CANCELLED",
                "cancelled_by": user.id,
                "cancelled_at": now(),
                "updated_at": now(),
            },
            "$inc": {"membership_revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not membership:
        raise HTTPException(status_code=409, detail={"code": "INVITATION_NOT_PENDING"})
    await audit(
        user.id, "project_invitation_cancelled", "ProjectMember", membership["_id"], project_id
    )
    return envelope(membership, revision=membership["membership_revision"])


@router.patch("/du-an/{project_id}/thanh-vien/{member_user_id}")
async def update_project_member(
    project_id: str,
    member_user_id: str,
    payload: ProjectMemberPatch,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.members.manage")
    previous = await database.value.project_members.find_one(
        {"project_id": project_id, "user_id": member_user_id}
    )
    if not previous:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    if previous.get("membership_revision") != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "REVISION_CONFLICT",
                "current_revision": previous.get("membership_revision"),
            },
        )
    changes = {
        key: value
        for key, value in payload.model_dump().items()
        if value is not None and key != "expected_revision"
    }
    desired_role = changes.get("project_role", previous.get("project_role"))
    desired_status = changes.get("status", previous.get("status"))
    was_active_lead = (
        previous.get("project_role") == "QA_LEAD" and previous.get("status") == "ACTIVE"
    )
    remains_active_lead = desired_role == "QA_LEAD" and desired_status == "ACTIVE"
    if was_active_lead and not remains_active_lead:
        lead_count = await database.value.project_members.count_documents(
            {"project_id": project_id, "project_role": "QA_LEAD", "status": "ACTIVE"}
        )
        if lead_count <= 1:
            raise HTTPException(status_code=422, detail={"code": "PROJECT_LAST_QA_LEAD_REQUIRED"})
    changes["updated_at"] = now()
    membership = await database.value.project_members.find_one_and_update(
        {
            "project_id": project_id,
            "user_id": member_user_id,
            "membership_revision": payload.expected_revision,
        },
        {"$set": changes, "$inc": {"membership_revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not membership:
        existing = await database.value.project_members.find_one(
            {"project_id": project_id, "user_id": member_user_id}
        )
        if not existing:
            raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
        raise HTTPException(
            status_code=409,
            detail={
                "code": "REVISION_CONFLICT",
                "current_revision": existing["membership_revision"],
            },
        )
    remains_active_lead = (
        membership.get("project_role") == "QA_LEAD" and membership.get("status") == "ACTIVE"
    )
    if was_active_lead and not remains_active_lead:
        lead_count = await database.value.project_members.count_documents(
            {"project_id": project_id, "project_role": "QA_LEAD", "status": "ACTIVE"}
        )
        if lead_count == 0:
            await database.value.project_members.update_one(
                {
                    "_id": membership["_id"],
                    "project_id": project_id,
                    "membership_revision": membership["membership_revision"],
                },
                {
                    "$set": {
                        "project_role": previous["project_role"],
                        "status": previous["status"],
                        "updated_at": now(),
                    },
                    "$inc": {"membership_revision": 1},
                },
            )
            raise HTTPException(status_code=422, detail={"code": "PROJECT_LAST_QA_LEAD_REQUIRED"})
    await audit(
        user.id,
        "project_member_updated",
        "ProjectMember",
        membership["_id"],
        project_id,
        {"user_id": member_user_id, **changes},
    )
    return envelope(membership, revision=membership["membership_revision"])


@router.delete("/du-an/{project_id}/thanh-vien/{member_user_id}")
async def remove_project_member(
    project_id: str, member_user_id: str, user: CurrentUser = Depends(get_current_user)
):
    await get_project(project_id, user, "project.members.manage")
    membership = await database.value.project_members.find_one(
        {"project_id": project_id, "user_id": member_user_id}
    )
    if not membership:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    if membership.get("project_role") == "QA_LEAD" and membership.get("status") == "ACTIVE":
        lead_count = await database.value.project_members.count_documents(
            {"project_id": project_id, "project_role": "QA_LEAD", "status": "ACTIVE"}
        )
        if lead_count <= 1:
            raise HTTPException(status_code=422, detail={"code": "PROJECT_LAST_QA_LEAD_REQUIRED"})
    await database.value.project_members.delete_one(
        {"project_id": project_id, "user_id": member_user_id}
    )
    await audit(
        user.id,
        "project_member_removed",
        "ProjectMember",
        membership["_id"],
        project_id,
        {"user_id": member_user_id},
    )
    return envelope({"removed": True, "user_id": member_user_id})
