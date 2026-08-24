from fastapi import APIRouter, Depends, Query
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user, require_contributor
from src.core.common import audit, envelope, get_project, new_id, now, optimistic_patch
from src.core.database import database
from src.domain.schemas import ProjectCreate, ProjectPatch


router = APIRouter(prefix="/api/qa", tags=["QA Projects"])


@router.post("/projects", status_code=201)
async def create_project(
    payload: ProjectCreate,
    user: CurrentUser = Depends(require_contributor),
):
    timestamp = now()
    project = {
        "_id": new_id("PRJ"),
        **payload.model_dump(),
        "owner_id": user.id,
        "member_roles": {user.id: "qa_lead"},
        "status": "active",
        "revision": 1,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.projects.insert_one(project)
    except DuplicateKeyError:
        from fastapi import HTTPException

        raise HTTPException(status_code=409, detail={"code": "PROJECT_KEY_EXISTS"})
    await audit(user.id, "project_created", "Project", project["_id"], project["_id"])
    return envelope(project, revision=1)


@router.get("/projects")
async def list_projects(
    q: str = Query(default="", max_length=200),
    status: str = Query(default="active", max_length=30),
    limit: int = Query(default=50, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
):
    membership = {
        "$or": [
            {"owner_id": user.id},
            {f"member_roles.{user.id}": {"$exists": True}},
        ]
    }
    query = {} if user.is_admin else membership
    if status:
        query["status"] = status
    if q:
        query["$and"] = [
            {"$or": [{"name": {"$regex": q, "$options": "i"}}, {"key": {"$regex": q, "$options": "i"}}]}
        ]
    items = await database.value.projects.find(query).sort("updated_at", -1).to_list(limit)
    return envelope(items)


@router.get("/projects/{project_id}")
async def project_detail(project_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await get_project(project_id, user))


@router.patch("/projects/{project_id}")
async def update_project(
    project_id: str,
    payload: ProjectPatch,
    user: CurrentUser = Depends(get_current_user),
):
    project = await get_project(project_id, user, write=True)
    if payload.member_roles is not None and not (
        user.is_admin or project.get("owner_id") == user.id
    ):
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="Chỉ QA Lead được thay đổi thành viên")
    updated = await optimistic_patch(
        "projects",
        project_id,
        project_id,
        payload.expected_revision,
        payload.model_dump(),
    )
    await audit(user.id, "project_updated", "Project", project_id, project_id)
    return envelope(updated, revision=updated["revision"])
