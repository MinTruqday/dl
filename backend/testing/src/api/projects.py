from fastapi import APIRouter, Depends, HTTPException, Query
import os
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user, permissions_for_role
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


router = APIRouter(prefix="/api/qa", tags=["QA Projects"])


@router.post("/projects", status_code=201)
async def create_project(
    payload: ProjectCreate,
    user: CurrentUser = Depends(get_current_user),
):
    policy = settings.PROJECT_CREATION_POLICY
    authentication_db = os.environ.get("AUTHENTICATION_DB_NAME")
    if authentication_db:
        config = await database.client[authentication_db].system_configs.find_one(
            {"type": "project_creation"}
        )
        if config:
            policy = config.get("project_creation_policy", policy)
    if policy == "ADMIN_ONLY" and not user.is_system_admin:
        raise HTTPException(
            status_code=403,
            detail={"code": "SYSTEM_PERMISSION_DENIED"},
        )
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


@router.get("/projects")
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
    query = {"_id": {"$in": list(by_project)}}
    if status:
        query["status"] = status
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"key": {"$regex": q, "$options": "i"}},
        ]
    projects = await database.value.projects.find(query).sort("updated_at", -1).to_list(limit)
    items = [
        {
            **project,
            "current_membership": by_project[project["_id"]],
            "current_permissions": sorted(
                permissions_for_role(
                    by_project[project["_id"]]["project_role"],
                    project.get("settings"),
                )
            ),
        }
        for project in projects
    ]
    return envelope(items)


@router.get("/projects/{project_id}")
async def project_detail(project_id: str, user: CurrentUser = Depends(get_current_user)):
    project = await get_project(project_id, user, "project.read")
    membership = await database.value.project_members.find_one(
        {"project_id": project_id, "user_id": user.id, "status": "ACTIVE"}
    )
    return envelope(
        {
            **project,
            "current_membership": membership,
            "current_permissions": sorted(
                permissions_for_role(
                    membership["project_role"],
                    project.get("settings"),
                )
            ),
        }
    )


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: str,
    payload: ProjectPatch,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.update")
    updated = await optimistic_patch(
        "projects",
        project_id,
        project_id,
        payload.expected_revision,
        payload.model_dump(),
    )
    await audit(user.id, "project_updated", "Project", project_id, project_id)
    return envelope(updated, revision=updated["revision"])


@router.post("/projects/{project_id}/archive")
async def archive_project(
    project_id: str,
    payload: ProjectArchiveInput,
    user: CurrentUser = Depends(get_current_user),
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
        user.id,
        "project_archived",
        "Project",
        project_id,
        project_id,
        {"reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/projects/{project_id}/restore")
async def restore_project(
    project_id: str,
    payload: ProjectArchiveInput,
    user: CurrentUser = Depends(get_current_user),
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
        user.id,
        "project_restored",
        "Project",
        project_id,
        project_id,
        {"reason": payload.reason},
    )
    return envelope(updated, revision=updated["revision"])


@router.get("/projects/{project_id}/members")
async def list_project_members(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.members.read")
    members = await database.value.project_members.find({"project_id": project_id}).sort(
        "created_at", 1
    ).to_list(5000)
    return envelope(members)


@router.post("/projects/{project_id}/members", status_code=201)
async def add_project_member(
    project_id: str,
    payload: ProjectMemberCreate,
    user: CurrentUser = Depends(get_current_user),
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
        raise HTTPException(
            status_code=409,
            detail={"code": "PROJECT_MEMBERSHIP_EXISTS"},
        )
    await audit(
        user.id,
        "project_member_added",
        "ProjectMember",
        membership["_id"],
        project_id,
        {"user_id": payload.user_id, "project_role": payload.project_role},
    )
    return envelope(membership, revision=1)


@router.post("/projects/{project_id}/invitations", status_code=201)
async def invite_project_member(
    project_id: str,
    payload: ProjectMemberCreate,
    user: CurrentUser = Depends(get_current_user),
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


@router.post("/projects/{project_id}/members/{member_user_id}/accept")
async def accept_project_invitation(
    project_id: str,
    member_user_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    if user.id != member_user_id:
        raise HTTPException(status_code=403, detail={"code": "INVITATION_OWNER_REQUIRED"})
    membership = await database.value.project_members.find_one_and_update(
        {"project_id": project_id, "user_id": user.id, "status": "INVITED"},
        {
            "$set": {"status": "ACTIVE", "accepted_at": now(), "updated_at": now()},
            "$inc": {"membership_revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not membership:
        raise HTTPException(status_code=404, detail={"code": "INVITATION_NOT_FOUND"})
    await audit(
        user.id,
        "project_invitation_accepted",
        "ProjectMember",
        membership["_id"],
        project_id,
    )
    return envelope(membership, revision=membership["membership_revision"])


@router.post("/projects/{project_id}/members/{member_user_id}/resend-invite")
async def resend_project_invitation(
    project_id: str,
    member_user_id: str,
    user: CurrentUser = Depends(get_current_user),
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
        user.id,
        "project_invitation_resent",
        "ProjectMember",
        membership["_id"],
        project_id,
    )
    return envelope(membership, revision=membership["membership_revision"])


@router.post("/projects/{project_id}/members/{member_user_id}/cancel-invite")
async def cancel_project_invitation(
    project_id: str,
    member_user_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.members.manage")
    membership = await database.value.project_members.find_one_and_update(
        {"project_id": project_id, "user_id": member_user_id, "status": "INVITED"},
        {
            "$set": {"status": "CANCELLED", "cancelled_by": user.id, "cancelled_at": now(), "updated_at": now()},
            "$inc": {"membership_revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not membership:
        raise HTTPException(status_code=409, detail={"code": "INVITATION_NOT_PENDING"})
    await audit(
        user.id,
        "project_invitation_cancelled",
        "ProjectMember",
        membership["_id"],
        project_id,
    )
    return envelope(membership, revision=membership["membership_revision"])


@router.patch("/projects/{project_id}/members/{member_user_id}")
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
    was_active_lead = previous.get("project_role") == "QA_LEAD" and previous.get("status") == "ACTIVE"
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
    remains_active_lead = membership.get("project_role") == "QA_LEAD" and membership.get("status") == "ACTIVE"
    if was_active_lead and not remains_active_lead:
        lead_count = await database.value.project_members.count_documents(
            {"project_id": project_id, "project_role": "QA_LEAD", "status": "ACTIVE"}
        )
        if lead_count == 0:
            await database.value.project_members.update_one(
                {"_id": membership["_id"], "project_id": project_id, "membership_revision": membership["membership_revision"]},
                {"$set": {"project_role": previous["project_role"], "status": previous["status"], "updated_at": now()}, "$inc": {"membership_revision": 1}},
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


@router.delete("/projects/{project_id}/members/{member_user_id}")
async def remove_project_member(
    project_id: str,
    member_user_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "project.members.manage")
    membership = await database.value.project_members.find_one(
        {"project_id": project_id, "user_id": member_user_id}
    )
    if not membership:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    if membership.get("project_role") == "QA_LEAD" and membership.get("status") == "ACTIVE":
        lead_count = await database.value.project_members.count_documents(
            {
                "project_id": project_id,
                "project_role": "QA_LEAD",
                "status": "ACTIVE",
            }
        )
        if lead_count <= 1:
            raise HTTPException(
                status_code=422,
                detail={"code": "PROJECT_LAST_QA_LEAD_REQUIRED"},
            )
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
