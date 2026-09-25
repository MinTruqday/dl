from fastapi import HTTPException

from src.core.common import audit, get_project, get_project_entity, new_id, now, require_action_policy
from src.repositories.test_design import test_design_repository
from src.services.linters import lint_test_case
from src.services.domain_policy import domain_policy
from src.clients.project_knowledge import index_artifact
from src.services.test_case_records import project_test_text

LIFECYCLE_POLICY = domain_policy("test_case_lifecycle")


async def lint_test_case_draft_record(draft_id, user, project_id=None):
    draft = await get_project_entity(LIFECYCLE_POLICY["draft_collection"], draft_id, user, LIFECYCLE_POLICY["lint_permission"])
    await get_project(draft["project_id"], user, LIFECYCLE_POLICY["ai_lint_permission"])
    if project_id is not None and draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": LIFECYCLE_POLICY["project_mismatch_code"]})
    findings = lint_test_case(draft)
    result = {
        "test_case_draft_id": draft_id,
        "findings": findings,
        "valid": not any(
            item["severity"] == LIFECYCLE_POLICY["lint_blocking_severity"]
            for item in findings
        ),
        "model": {
            "provider": LIFECYCLE_POLICY["deterministic_provider"],
            "model": LIFECYCLE_POLICY["quality_model"],
            "prompt_version": LIFECYCLE_POLICY["prompt_version"],
            "tool_schema_version": LIFECYCLE_POLICY["tool_schema_version"],
            "retrieval_version": LIFECYCLE_POLICY["retrieval_version"],
        },
    }
    await test_design_repository.insert_ai_finding(
        {
            "_id": new_id(LIFECYCLE_POLICY["ai_finding_id_prefix"]),
            "project_id": draft["project_id"],
            "artifact_type": LIFECYCLE_POLICY["test_case_artifact_type"],
            "artifact_id": draft_id,
            **result,
            "created_at": now(),
        }
    )
    return result


async def submit_test_case_review_record(project_id, draft_id, payload, user):
    draft = await get_project_entity(LIFECYCLE_POLICY["draft_collection"], draft_id, user, LIFECYCLE_POLICY["submit_permission"])
    if draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": LIFECYCLE_POLICY["project_mismatch_code"]})
    if draft["status"] == LIFECYCLE_POLICY["review_status"]:
        return draft
    if draft["status"] != LIFECYCLE_POLICY["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": LIFECYCLE_POLICY["invalid_transition_code"]})
    if draft["revision"] != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["revision_conflict_code"], "current_revision": draft["revision"]},
        )
    findings = lint_test_case(draft)
    project_settings = await test_design_repository.find_project_settings(project_id)
    lint_blocking = project_settings.get(
        LIFECYCLE_POLICY["lint_setting"], LIFECYCLE_POLICY["lint_setting_default"]
    )
    if lint_blocking and any(
        item["severity"] == LIFECYCLE_POLICY["lint_blocking_severity"] for item in findings
    ):
        raise HTTPException(
            status_code=409, detail={"code": LIFECYCLE_POLICY["lint_blocked_code"], "findings": findings}
        )
    timestamp = now()
    transitioned = await test_design_repository.transition_case_draft(
        draft_id,
        project_id,
        payload.expected_revision,
        LIFECYCLE_POLICY["draft_status"],
        LIFECYCLE_POLICY["review_status"],
        {
            "review_note": payload.review_note,
            "review_submitted_by": user.id,
            "review_submitted_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not transitioned:
        raise HTTPException(status_code=409, detail={"code": LIFECYCLE_POLICY["revision_conflict_code"]})
    draft = await test_design_repository.find_case_draft(draft_id, project_id)
    await audit(
        user.id,
        LIFECYCLE_POLICY["review_submitted_event"],
        LIFECYCLE_POLICY["draft_entity"],
        draft_id,
        project_id,
        {"review_note": payload.review_note},
    )
    return draft


async def request_test_case_changes_record(project_id, draft_id, payload, user):
    draft = await get_project_entity(LIFECYCLE_POLICY["draft_collection"], draft_id, user, LIFECYCLE_POLICY["review_permission"])
    await require_action_policy(draft["project_id"], user, LIFECYCLE_POLICY["request_changes_action"], set(LIFECYCLE_POLICY["request_changes_roles"]))
    if draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": LIFECYCLE_POLICY["project_mismatch_code"]})
    if draft["status"] != LIFECYCLE_POLICY["review_status"]:
        raise HTTPException(status_code=409, detail={"code": LIFECYCLE_POLICY["invalid_transition_code"]})
    if draft["revision"] != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["revision_conflict_code"], "current_revision": draft["revision"]},
        )
    timestamp = now()
    transitioned = await test_design_repository.transition_case_draft(
        draft_id,
        project_id,
        payload.expected_revision,
        LIFECYCLE_POLICY["review_status"],
        LIFECYCLE_POLICY["draft_status"],
        {
            "review_note": payload.review_note,
            "changes_requested_by": user.id,
            "changes_requested_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not transitioned:
        raise HTTPException(status_code=409, detail={"code": LIFECYCLE_POLICY["revision_conflict_code"]})
    draft = await test_design_repository.find_case_draft(draft_id, project_id)
    await audit(
        user.id,
        LIFECYCLE_POLICY["changes_requested_event"],
        LIFECYCLE_POLICY["draft_entity"],
        draft_id,
        project_id,
        {"review_note": payload.review_note},
    )
    return draft


async def approve_test_case_draft_record(draft_id, payload, user):
    draft = await get_project_entity(LIFECYCLE_POLICY["draft_collection"], draft_id, user, LIFECYCLE_POLICY["approve_permission"])
    if draft["status"] == LIFECYCLE_POLICY["approved_status"] and draft.get(
        "frozen_version_id"
    ):
        return await approved_test_case_result(draft)
    if draft["status"] != LIFECYCLE_POLICY["review_status"]:
        raise HTTPException(status_code=409, detail={"code": LIFECYCLE_POLICY["invalid_transition_code"]})
    if draft["revision"] != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": LIFECYCLE_POLICY["revision_conflict_code"], "current_revision": draft["revision"]},
        )
    findings = lint_test_case(draft)
    project_settings = await test_design_repository.find_project_settings(draft["project_id"])
    lint_blocking = project_settings.get(
        LIFECYCLE_POLICY["lint_setting"], LIFECYCLE_POLICY["lint_setting_default"]
    )
    if lint_blocking and any(
        item["severity"] == LIFECYCLE_POLICY["lint_blocking_severity"] for item in findings
    ):
        raise HTTPException(
            status_code=409, detail={"code": LIFECYCLE_POLICY["lint_blocked_code"], "findings": findings}
        )
    claimed = await claim_test_case_draft(draft, payload, user)
    if not claimed:
        current = await test_design_repository.find_case_draft(
            draft_id, draft["project_id"]
        )
        if (
            current
            and current.get("status") == LIFECYCLE_POLICY["approved_status"]
            and current.get("frozen_version_id")
        ):
            return await approved_test_case_result(current)
        raise HTTPException(status_code=409, detail={"code": LIFECYCLE_POLICY["approval_in_progress_code"]})
    test_case, version = await persist_test_case_version(claimed, payload, user)
    trace_ready = True
    try:
        await create_suggested_trace_records(claimed, version, user)
    except Exception:
        trace_ready = False
    indexed = await index_artifact(
        version["project_id"],
        LIFECYCLE_POLICY["version_artifact_type"],
        version["test_case_id"],
        version["_id"],
        version["title"],
        version["plain_text_projection"],
        version["status"],
        LIFECYCLE_POLICY["approved_authority"],
        version["version"],
        requirement_version_ids=version.get("requirement_version_ids", []),
        acceptance_criterion_ids=version.get("acceptance_criterion_ids", []),
    )
    await audit(
        user.id,
        LIFECYCLE_POLICY["version_approved_event"],
        LIFECYCLE_POLICY["version_entity"],
        version["_id"],
        claimed["project_id"],
        {"draft_id": draft_id},
    )
    ready = trace_ready and indexed
    return {
        "data": {"test_case": {**test_case, "current_version_id": version["_id"]}, "version": version},
        "status": LIFECYCLE_POLICY["success_status"] if ready else LIFECYCLE_POLICY["degraded_status"],
        "degraded_mode": None if ready else LIFECYCLE_POLICY["degraded_derived_data_mode"],
    }


async def claim_test_case_draft(draft, payload, user):
    timestamp = now()
    return await test_design_repository.claim_case_draft(
        draft["_id"],
        draft["project_id"],
        payload.expected_revision,
        LIFECYCLE_POLICY["review_status"],
        LIFECYCLE_POLICY["approving_status"],
        {
            "approval_started_by": user.id,
            "approval_started_at": timestamp,
            "updated_at": timestamp,
        },
    )


async def approved_test_case_result(draft):
    version = await test_design_repository.find_case_version(
        draft["frozen_version_id"], draft["project_id"]
    )
    test_case = await test_design_repository.find_case(
        version["test_case_id"], draft["project_id"]
    )
    return {"data": {"test_case": test_case, "version": version}, "status": LIFECYCLE_POLICY["success_status"], "degraded_mode": None}


async def persist_test_case_version(draft, payload, user):
    timestamp = now()
    test_case = None
    version = None
    parent_version_id = None
    created_test_case = False
    try:
        existing = await test_design_repository.find_case_by_key(
            draft["project_id"], draft["test_case_key"]
        )
        if existing:
            latest = await test_design_repository.find_latest_case_version(existing["_id"])
            if not latest:
                raise HTTPException(status_code=409, detail={"code": LIFECYCLE_POLICY["version_history_invalid_code"]})
            test_case = existing
            version_number = int(latest["version"]) + 1
            parent_version_id = latest["_id"]
        else:
            test_case = {
                "_id": new_id(LIFECYCLE_POLICY["case_id_prefix"]),
                "project_id": draft["project_id"],
                "test_case_key": draft["test_case_key"],
                "current_version_id": None,
                "status": LIFECYCLE_POLICY["active_status"],
                "owner_id": draft.get("owner_id") or draft.get("created_by"),
                "tags": draft.get("tags", []),
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            await test_design_repository.insert_case(test_case)
            created_test_case = True
            version_number = 1
        version = build_test_case_version(
            draft, test_case["_id"], version_number, parent_version_id, payload, user, timestamp
        )
        await test_design_repository.insert_case_version(version)
        updated_case = await test_design_repository.activate_case_version(
            test_case["_id"],
            draft["project_id"],
            parent_version_id,
            version["_id"],
            LIFECYCLE_POLICY["active_status"],
            timestamp,
        )
        if not updated_case:
            raise HTTPException(status_code=409, detail={"code": LIFECYCLE_POLICY["version_conflict_code"]})
        updated_draft = await test_design_repository.approve_case_draft(
            draft["_id"],
            draft["project_id"],
            draft["revision"],
            LIFECYCLE_POLICY["approving_status"],
            LIFECYCLE_POLICY["approved_status"],
            version["_id"],
            timestamp,
        )
        if not updated_draft:
            raise HTTPException(status_code=409, detail={"code": LIFECYCLE_POLICY["approval_conflict_code"]})
        return test_case, version
    except Exception:
        await rollback_test_case_version(draft, test_case, version, parent_version_id, created_test_case)
        raise


def build_test_case_version(draft, test_case_id, version_number, parent_version_id, payload, user, timestamp):
    return {
        "_id": new_id(LIFECYCLE_POLICY["version_id_prefix"]),
        "project_id": draft["project_id"],
        "test_case_id": test_case_id,
        "test_case_key": draft["test_case_key"],
        "version": version_number,
        "title": draft["title"],
        "type": draft["type"],
        "priority": draft["priority"],
        "risk": draft["risk"],
        "objective_doc": draft.get("objective_doc", {"type": "doc", "content": []}),
        "preconditions_doc": draft["preconditions_doc"],
        "steps": draft["steps"],
        "test_data": draft["test_data"],
        "expected_result_doc": draft["expected_result_doc"],
        "postconditions_doc": draft["postconditions_doc"],
        "tags": draft["tags"],
        "owner_id": draft.get("owner_id") or draft.get("created_by"),
        "techniques": draft.get("techniques", []),
        "automation_status": draft["automation_status"],
        "attachments": draft.get("attachments", []),
        "data_set_version_ids": draft.get("data_set_version_ids", []),
        "requirement_version_ids": draft["requirement_version_ids"],
        "acceptance_criterion_ids": draft["acceptance_criterion_ids"],
        "scenario_id": draft.get("scenario_id"),
        "source_evidence": draft.get("source_evidence", []),
        "plain_text_projection": project_test_text(draft),
        "parent_version_id": parent_version_id,
        "change_reason": payload.change_reason,
        "review_note": payload.review_note,
        "status": LIFECYCLE_POLICY["active_status"],
        "approved_by": user.id,
        "created_at": timestamp,
    }


async def rollback_test_case_version(draft, test_case, version, parent_version_id, created_test_case):
    if version:
        await test_design_repository.delete_case_version(version["_id"], draft["project_id"])
    if test_case and created_test_case:
        await test_design_repository.delete_unactivated_case(
            test_case["_id"],
            draft["project_id"],
            [None, version["_id"] if version else None],
        )
    elif test_case and version:
        await test_design_repository.restore_case_version(
            test_case["_id"],
            draft["project_id"],
            version["_id"],
            parent_version_id,
            now(),
        )
    await test_design_repository.reset_case_draft(
        draft["_id"],
        draft["project_id"],
        LIFECYCLE_POLICY["approving_status"],
        LIFECYCLE_POLICY["review_status"],
        now(),
    )


async def create_suggested_trace_records(draft, version, user):
    trace_policy = domain_policy("trace_suggestion")
    sources = [
        (LIFECYCLE_POLICY["requirement_source_type"], source_id)
        for source_id in draft.get("requirement_version_ids", [])
    ] + [
        (LIFECYCLE_POLICY["criterion_source_type"], source_id)
        for source_id in draft.get("acceptance_criterion_ids", [])
    ]
    for source_type, source_id in sources:
        exists = await test_design_repository.find_trace_link(
            {
                "project_id": draft["project_id"],
                "source_type": source_type,
                "source_id": source_id,
                "target_type": LIFECYCLE_POLICY["trace_target_type"],
                "target_id": version["_id"],
            }
        )
        if exists:
            continue
        ai_generated = draft.get("origin") == LIFECYCLE_POLICY["ai_origin"]
        await test_design_repository.insert_trace_link(
            {
                "_id": new_id(LIFECYCLE_POLICY["trace_id_prefix"]),
                "project_id": draft["project_id"],
                "source_type": source_type,
                "source_id": source_id,
                "target_type": LIFECYCLE_POLICY["trace_target_type"],
                "target_id": version["_id"],
                "link_type": LIFECYCLE_POLICY["trace_link_type"],
                "confidence": trace_policy["ai_confidence"]
                if ai_generated
                else trace_policy["manual_confidence"],
                "origin": LIFECYCLE_POLICY["ai_trace_origin"]
                if ai_generated
                else LIFECYCLE_POLICY["manual_trace_origin"],
                "status": LIFECYCLE_POLICY["suggested_trace_status"]
                if ai_generated
                else LIFECYCLE_POLICY["confirmed_trace_status"],
                "revision": LIFECYCLE_POLICY["initial_revision"],
                "evidence": draft.get("source_evidence", []),
                "created_by": user.id,
                "created_at": now(),
            }
        )
