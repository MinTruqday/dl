from fastapi import HTTPException

from src.core.common import (
    audit,
    get_project,
    get_project_entity,
    new_id,
    next_key,
    now,
    optimistic_patch,
    plain_text,
)
from src.repositories import test_design_repository
from src.services.domain_policy import domain_policy


def project_test_text(value):
    steps = " ".join(
        f"{plain_text(step.get('action_doc', {}))} {plain_text(step.get('expected_doc', {}))}"
        for step in value.get("steps", [])
    )
    return " ".join(
        [
            value.get("title", ""),
            plain_text(value.get("objective_doc", {})),
            plain_text(value.get("preconditions_doc", {})),
            steps,
            plain_text(value.get("expected_result_doc", {})),
        ]
    ).strip()


async def validate_design_sources(
    project_id,
    requirement_version_ids,
    acceptance_criterion_ids,
    scenario_id=None,
    test_condition_ids=None,
):
    policy = domain_policy("test_case_records")
    requirement_ids = list(dict.fromkeys(requirement_version_ids or []))
    criterion_ids = list(dict.fromkeys(acceptance_criterion_ids or []))
    if requirement_ids:
        count = await test_design_repository.count_requirement_versions(
            project_id, requirement_ids
        )
        if count != len(requirement_ids):
            raise HTTPException(
                status_code=422, detail={"code": policy["missing_requirement_code"]}
            )
    if criterion_ids:
        query = {"project_id": project_id, "_id": {"$in": criterion_ids}}
        if requirement_ids:
            query["requirement_version_id"] = {"$in": requirement_ids}
        count = await test_design_repository.count_acceptance_criteria(query)
        if count != len(criterion_ids):
            raise HTTPException(
                status_code=422, detail={"code": policy["missing_criterion_code"]}
            )
    if scenario_id:
        scenario = await test_design_repository.find_scenario(
            scenario_id, project_id
        )
        if not scenario:
            raise HTTPException(
                status_code=422, detail={"code": policy["missing_scenario_code"]}
            )
    condition_ids = list(dict.fromkeys(test_condition_ids or []))
    if condition_ids:
        settings = await test_design_repository.find_project_settings(project_id)
        query = {
            "project_id": project_id,
            "_id": {"$in": condition_ids},
            "status": {"$ne": policy["archived_status"]},
        }
        conditions = await test_design_repository.list_conditions(query, len(condition_ids))
        found_ids = {item["_id"] for item in conditions}
        missing_ids = [
            condition_id for condition_id in condition_ids if condition_id not in found_ids
        ]
        if missing_ids:
            raise HTTPException(
                status_code=422,
                detail={"code": policy["condition_not_found_code"], "condition_ids": missing_ids},
            )
        strict = settings.get(
            policy["approval_setting"],
            settings.get(policy["legacy_approval_setting"], False),
        )
        unapproved_ids = [
            item["_id"]
            for item in conditions
            if item.get("status") != policy["approved_status"]
        ]
        if strict and unapproved_ids:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": policy["condition_not_approved_code"],
                    "condition_ids": unapproved_ids,
                },
            )


async def validate_data_set_versions(project_id, data_set_version_ids):
    policy = domain_policy("test_case_records")
    version_ids = list(dict.fromkeys(data_set_version_ids or []))
    if not version_ids:
        return
    count = await test_design_repository.count_data_set_versions(
        project_id, version_ids
    )
    if count != len(version_ids):
        raise HTTPException(
            status_code=422, detail={"code": policy["missing_data_set_code"]}
        )


async def create_test_case_draft_record(project_id, payload, user):
    policy = domain_policy("test_case_records")
    await get_project(project_id, user, "testcase.create")
    await validate_design_sources(
        project_id,
        payload.requirement_version_ids,
        payload.acceptance_criterion_ids,
        payload.scenario_id,
        payload.test_condition_ids,
    )
    await validate_data_set_versions(project_id, payload.data_set_version_ids)
    draft = {
        "_id": new_id(policy["draft_id_prefix"]),
        "project_id": project_id,
        **payload.model_dump(),
        "test_case_key": payload.test_case_key
        or await next_key(project_id, policy["counter_name"], policy["key_prefix"]),
        "status": policy["draft_status"],
        "revision": 1,
        "created_by": user.id,
        "created_at": now(),
        "updated_at": now(),
    }
    await test_design_repository.insert_case_draft(draft)
    await audit(user.id, "test_case_draft_created", "TestCaseDraft", draft["_id"], project_id)
    return draft


async def update_test_case_draft_record(draft_id, payload, user, project_id=None):
    policy = domain_policy("test_case_records")
    draft = await get_project_entity("test_case_drafts", draft_id, user, "testcase.update")
    if project_id is not None and draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    if draft["status"] != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["immutable_draft_code"]})
    if payload.attachments is not None:
        await get_project(draft["project_id"], user, "attachment.manage")
    await validate_design_sources(
        draft["project_id"],
        payload.requirement_version_ids
        if payload.requirement_version_ids is not None
        else draft.get("requirement_version_ids", []),
        payload.acceptance_criterion_ids
        if payload.acceptance_criterion_ids is not None
        else draft.get("acceptance_criterion_ids", []),
        payload.scenario_id if payload.scenario_id is not None else draft.get("scenario_id"),
    )
    await validate_data_set_versions(
        draft["project_id"],
        payload.data_set_version_ids
        if payload.data_set_version_ids is not None
        else draft.get("data_set_version_ids", []),
    )
    updated = await optimistic_patch(
        "test_case_drafts",
        draft_id,
        draft["project_id"],
        payload.expected_revision,
        payload.model_dump(),
    )
    await audit(user.id, "test_case_draft_updated", "TestCaseDraft", draft_id, draft["project_id"])
    return updated
