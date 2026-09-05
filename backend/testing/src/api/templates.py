from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo import ReturnDocument

from src.core.auth import CurrentUser, get_current_user
from src.core.common import (
    audit,
    envelope,
    get_project,
    get_project_entity,
    new_id,
    now,
    require_action_policy,
)
from src.core.database import database


class TestCaseTemplateCreate(BaseModel):
    name: str = Field(min_length=2, max_length=300)
    template_type: Literal["functional", "api", "rbac", "state", "bva"]
    description: str = Field(default="", max_length=5000)
    definition: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list, max_length=100)


class TestCaseTemplatePatch(BaseModel):
    expected_revision: int = Field(ge=1)
    name: str | None = Field(default=None, min_length=2, max_length=300)
    template_type: Literal["functional", "api", "rbac", "state", "bva"] | None = None
    description: str | None = Field(default=None, max_length=5000)
    definition: dict[str, Any] | None = None
    tags: list[str] | None = Field(default=None, max_length=100)


class TestCaseTemplateArchive(BaseModel):
    expected_revision: int = Field(ge=1)
    reason: str = Field(min_length=2, max_length=2000)


router = APIRouter(prefix="/kiem-thu", tags=["Mẫu ca kiểm thử"])


@router.get(
    "/du-an/{project_id}/mau-ca-kiem-thu",
    openapi_extra={"x-function-ids": ["TPLT-01"]},
)
async def list_templates(
    project_id: str,
    template_type: Literal["functional", "api", "rbac", "state", "bva"] | None = Query(
        default=None
    ),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.template.read")
    query = {"project_id": project_id, "status": "ACTIVE"}
    if template_type:
        query["template_type"] = template_type
    items = await database.value.test_case_templates.find(query).sort("updated_at", -1).to_list(500)
    return envelope(items)


@router.get(
    "/mau-ca-kiem-thu/{template_id}",
    openapi_extra={"x-function-ids": ["TPLT-01"]},
)
async def get_template(template_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(
        await get_project_entity("test_case_templates", template_id, user, "testcase.template.read")
    )


@router.post(
    "/du-an/{project_id}/mau-ca-kiem-thu",
    status_code=201,
    openapi_extra={"x-function-ids": ["TPLT-02"]},
)
async def create_template(
    project_id: str,
    payload: TestCaseTemplateCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.template.manage")
    timestamp = now()
    template = {
        "_id": new_id("TPL"),
        "project_id": project_id,
        **payload.model_dump(),
        "status": "ACTIVE",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await database.value.test_case_templates.insert_one(template)
    except Exception as error:
        if getattr(error, "code", None) == 11000:
            raise HTTPException(status_code=409, detail={"code": "TEMPLATE_NAME_EXISTS"}) from error
        raise
    await audit(user.id, "test_case_template_created", "TestCaseTemplate", template["_id"], project_id)
    return envelope(template, revision=1)


@router.patch(
    "/mau-ca-kiem-thu/{template_id}",
    openapi_extra={"x-function-ids": ["TPLT-02"]},
)
async def update_template(
    template_id: str,
    payload: TestCaseTemplatePatch,
    user: CurrentUser = Depends(get_current_user),
):
    template = await get_project_entity(
        "test_case_templates", template_id, user, "testcase.template.manage"
    )
    if template.get("status") != "ACTIVE":
        raise HTTPException(status_code=409, detail={"code": "TEMPLATE_ARCHIVED"})
    changes = {key: value for key, value in payload.model_dump().items() if key != "expected_revision" and value is not None}
    updated = await database.value.test_case_templates.find_one_and_update(
        {
            "_id": template_id,
            "project_id": template["project_id"],
            "status": "ACTIVE",
            "revision": payload.expected_revision,
        },
        {"$set": {**changes, "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "test_case_template_updated", "TestCaseTemplate", template_id, template["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post(
    "/mau-ca-kiem-thu/{template_id}/luu-tru",
    openapi_extra={"x-function-ids": ["TPLT-03"]},
)
async def archive_template(
    template_id: str,
    payload: TestCaseTemplateArchive,
    user: CurrentUser = Depends(get_current_user),
):
    template = await get_project_entity(
        "test_case_templates", template_id, user, "testcase.template.manage"
    )
    await require_action_policy(
        template["project_id"], user, "testcase.template.archive", {"QA_LEAD"}
    )
    if template.get("status") == "ARCHIVED":
        return envelope(template, revision=template.get("revision", 1))
    updated = await database.value.test_case_templates.find_one_and_update(
        {
            "_id": template_id,
            "project_id": template["project_id"],
            "status": "ACTIVE",
            "revision": payload.expected_revision,
        },
        {
            "$set": {"status": "ARCHIVED", "archive_reason": payload.reason, "updated_at": now()},
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(user.id, "test_case_template_archived", "TestCaseTemplate", template_id, template["project_id"], {"reason": payload.reason})
    return envelope(updated, revision=updated["revision"])
