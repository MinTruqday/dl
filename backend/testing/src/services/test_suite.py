import re

from fastapi import HTTPException

from src.core.common import (
    audit,
    get_project,
    get_project_entity,
    new_id,
    now,
    optimistic_patch,
    sort_spec,
)
from src.repositories import test_design_repository
from src.services.domain_policy import domain_policy
from src.services.execution_policy import validate_test_versions


TEST_DESIGN_POLICY = domain_policy("test_design")


async def create_test_suite_record(payload, project_id, user):
    if project_id and project_id != payload.project_id:
        raise HTTPException(status_code=422, detail={"code": TEST_DESIGN_POLICY["project_scope_mismatch_code"]})
    await get_project(payload.project_id, user, "testsuite.create")
    await validate_test_versions(payload.project_id, payload.test_case_version_ids)
    timestamp = now()
    suite = {
        "_id": new_id(TEST_DESIGN_POLICY["suite_id_prefix"]),
        **payload.model_dump(),
        "status": TEST_DESIGN_POLICY["active_status"],
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await test_design_repository.insert_suite(suite)
    await audit(user.id, "test_suite_created", "TestSuite", suite["_id"], payload.project_id)
    return suite


async def list_test_suite_records(
    project_id,
    user,
    q="",
    suite_type="",
    status="",
    sort="-updated_at",
):
    await get_project(project_id, user, "testsuite.read")
    query = {"project_id": project_id}
    if q:
        query["name"] = {"$regex": re.escape(q), "$options": "i"}
    for field, value in {"suite_type": suite_type, "status": status}.items():
        if value:
            query[field] = value
    sort_field, direction = sort_spec(
        sort,
        set(TEST_DESIGN_POLICY["suite_sort_fields"]),
    )
    return await test_design_repository.list_suites(query, sort_field, direction)


async def get_test_suite_record(suite_id, user, permission="testsuite.read"):
    return await get_project_entity("test_suites", suite_id, user, permission)


async def update_test_suite_record(suite_id, payload, user):
    suite = await get_test_suite_record(suite_id, user, "testsuite.update")
    if suite.get("status", TEST_DESIGN_POLICY["active_status"]) == TEST_DESIGN_POLICY["archived_status"]:
        raise HTTPException(status_code=409, detail={"code": TEST_DESIGN_POLICY["suite_archived_code"]})
    if payload.test_case_version_ids is not None:
        await validate_test_versions(suite["project_id"], payload.test_case_version_ids)
    updated = await optimistic_patch(
        "test_suites",
        suite_id,
        suite["project_id"],
        payload.expected_revision,
        payload.model_dump(),
    )
    await audit(user.id, "test_suite_updated", "TestSuite", suite_id, suite["project_id"])
    return updated


async def clone_test_suite_record(suite_id, user):
    suite = await get_test_suite_record(suite_id, user, "testsuite.clone")
    timestamp = now()
    cloned = {
        **suite,
        "_id": new_id(TEST_DESIGN_POLICY["suite_id_prefix"]),
        "name": f"{suite['name']} bản sao",
        "status": TEST_DESIGN_POLICY["active_status"],
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    for field in ("archived_at", "archived_by", "archive_reason"):
        cloned.pop(field, None)
    await test_design_repository.insert_suite(cloned)
    await audit(
        user.id,
        "test_suite_cloned",
        "TestSuite",
        cloned["_id"],
        suite["project_id"],
        {"source_suite_id": suite_id},
    )
    return cloned


async def archive_test_suite_record(suite_id, payload, user):
    suite = await get_test_suite_record(suite_id, user, "testsuite.archive")
    updated = await optimistic_patch(
        "test_suites",
        suite_id,
        suite["project_id"],
        payload.expected_revision,
        {
            "status": TEST_DESIGN_POLICY["archived_status"],
            "archive_reason": payload.reason,
            "archived_by": user.id,
            "archived_at": now(),
        },
    )
    await audit(user.id, "test_suite_archived", "TestSuite", suite_id, suite["project_id"])
    return updated
