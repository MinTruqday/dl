import re

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.auth import CurrentUser, get_current_user
from src.core.common import (
    audit,
    envelope,
    get_project,
    get_project_entity,
    new_id,
    next_key,
    now,
    optimistic_patch,
    page_payload,
    plain_text,
    require_action_policy,
    sort_spec,
)
from src.core.database import database
from src.core.metrics import AI_GENERATION_LATENCY
from src.domain.schemas import (
    GenerateInput,
    ProjectArchiveInput,
    ReviewTransitionInput,
    ScenarioCreate,
    ScenarioPatch,
    TestCaseDraftCreate as CaseDraftCreate,
    TestCaseDraftPatch as CaseDraftPatch,
    TestCaseCloneInput,
    TestCaseFreezeInput as CaseFreezeInput,
    TestCaseGenerateInput,
)
from src.services.linters import duplicate_score, lint_test_case
from src.services.project_knowledge import index_artifact


router = APIRouter(prefix="/api/qa", tags=["QA Test Design"])


@router.post("/projects/{project_id}/test-scenarios", status_code=201)
async def create_scenario(
    project_id: str,
    payload: ScenarioCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testscenario.create")
    await validate_design_sources(
        project_id,
        payload.requirement_version_ids,
        payload.acceptance_criterion_ids,
    )
    scenario = {
        "_id": new_id("TS"),
        "project_id": project_id,
        **payload.model_dump(),
        "scenario_key": payload.scenario_key or await next_key(project_id, "scenario", "TS"),
        "revision": 1,
        "created_by": user.id,
        "created_at": now(),
        "updated_at": now(),
    }
    try:
        await database.value.test_scenarios.insert_one(scenario)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail={"code": "SCENARIO_KEY_EXISTS"})
    await audit(user.id, "test_scenario_created", "TestScenario", scenario["_id"], project_id)
    return envelope(scenario, revision=1)


@router.get("/projects/{project_id}/test-scenarios")
async def list_scenarios(
    project_id: str,
    q: str = Query(default="", max_length=300),
    status: str = Query(default="", max_length=30),
    category: str = Query(default="", max_length=50),
    risk: str = Query(default="", max_length=30),
    sort: str = Query(default="-updated_at", max_length=80),
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testscenario.read")
    query = {"project_id": project_id}
    if q:
        query["$or"] = [
            {"scenario_key": {"$regex": re.escape(q), "$options": "i"}},
            {"title": {"$regex": re.escape(q), "$options": "i"}},
        ]
    for field, value in {"status": status, "category": category, "risk": risk}.items():
        if value:
            query[field] = value
    sort_field, direction = sort_spec(
        sort, {"scenario_key", "title", "category", "risk", "status", "created_at", "updated_at"}
    )
    items = await database.value.test_scenarios.find(query).sort(sort_field, direction).to_list(limit)
    return envelope(items)


@router.get("/test-scenarios/{scenario_id}")
async def get_test_scenario(scenario_id: str, user: CurrentUser = Depends(get_current_user)):
    scenario = await get_project_entity("test_scenarios", scenario_id, user, "testscenario.read")
    cases = await database.value.test_cases.find({"project_id": scenario["project_id"], "scenario_id": scenario_id}).sort("test_case_key", 1).to_list(5000)
    return envelope({**scenario, "test_cases": cases})


@router.patch("/test-scenarios/{scenario_id}")
async def update_scenario(
    scenario_id: str,
    payload: ScenarioPatch,
    user: CurrentUser = Depends(get_current_user),
):
    scenario = await get_project_entity("test_scenarios", scenario_id, user, "testscenario.update")
    if scenario.get("status") != "draft":
        raise HTTPException(status_code=409, detail={"code": "IMMUTABLE_SCENARIO"})
    await validate_design_sources(
        scenario["project_id"],
        payload.requirement_version_ids if payload.requirement_version_ids is not None else scenario.get("requirement_version_ids", []),
        payload.acceptance_criterion_ids if payload.acceptance_criterion_ids is not None else scenario.get("acceptance_criterion_ids", []),
    )
    updated = await optimistic_patch(
        "test_scenarios", scenario_id, scenario["project_id"], payload.expected_revision, payload.model_dump()
    )
    await audit(user.id, "test_scenario_updated", "TestScenario", scenario_id, scenario["project_id"])
    return envelope(updated, revision=updated["revision"])


@router.post("/test-scenarios/{scenario_id}/clone", status_code=201)
async def clone_scenario(
    scenario_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    scenario = await get_project_entity(
        "test_scenarios", scenario_id, user, "testscenario.clone"
    )
    timestamp = now()
    cloned = {
        **scenario,
        "_id": new_id("TS"),
        "scenario_key": await next_key(scenario["project_id"], "scenario", "TS"),
        "title": f"{scenario['title']} bản sao",
        "status": "draft",
        "origin": "manual",
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await database.value.test_scenarios.insert_one(cloned)
    await audit(
        user.id,
        "test_scenario_cloned",
        "TestScenario",
        cloned["_id"],
        scenario["project_id"],
        {"source_scenario_id": scenario_id},
    )
    return envelope(cloned, revision=1)


@router.post("/test-scenarios/{scenario_id}/archive")
async def archive_scenario(
    scenario_id: str,
    payload: ProjectArchiveInput,
    user: CurrentUser = Depends(get_current_user),
):
    scenario = await get_project_entity(
        "test_scenarios", scenario_id, user, "testscenario.archive"
    )
    updated = await optimistic_patch(
        "test_scenarios",
        scenario_id,
        scenario["project_id"],
        payload.expected_revision,
        {
            "status": "archived",
            "archive_reason": payload.reason,
            "archived_by": user.id,
            "archived_at": now(),
        },
    )
    await audit(
        user.id,
        "test_scenario_archived",
        "TestScenario",
        scenario_id,
        scenario["project_id"],
    )
    return envelope(updated, revision=updated["revision"])


@router.post("/requirement-versions/{version_id}/ai/generate-scenarios", status_code=201)
async def generate_scenarios(
    version_id: str,
    payload: GenerateInput,
    user: CurrentUser = Depends(get_current_user),
):
    with AI_GENERATION_LATENCY.labels("scenario").time():
        version = await get_project_entity(
            "requirement_versions", version_id, user, "ai.generate_scenario"
        )
        criteria = await database.value.acceptance_criteria.find({"requirement_version_id": version_id}).to_list(500)
        categories = payload.categories or ["happy_path", "negative", "boundary", "validation"]
        created = []
        for category in categories:
            for number in range(payload.count_per_category):
                evidence = criteria[number % len(criteria)] if criteria else None
                scenario_payload = ScenarioCreate(
                    title=f"{category.replace('_', ' ').title()} cho {version['title']}",
                    objective=evidence.get("plain_text", "") if evidence else version["plain_text_projection"],
                    risk=version.get("risk", "medium"),
                    priority=version.get("priority", "medium"),
                    requirement_version_ids=[version_id],
                    acceptance_criterion_ids=[evidence["_id"]] if evidence else [],
                    origin="ai_generated",
                    category=category,
                )
                response = await create_scenario(version["project_id"], scenario_payload, user)
                created.append(response["data"])
    await audit(user.id, "test_scenarios_generated", "RequirementVersion", version_id, version["project_id"], {"count": len(created), "evidence_count": len(criteria)})
    return envelope({"items": created, "evidence": criteria, "model": model_metadata("scenario-generator-v1")})


@router.post("/projects/{project_id}/test-cases", status_code=201)
@router.post("/projects/{project_id}/test-case-drafts", status_code=201)
async def create_test_case_draft(
    project_id: str,
    payload: CaseDraftCreate,
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.create")
    await validate_design_sources(
        project_id,
        payload.requirement_version_ids,
        payload.acceptance_criterion_ids,
        payload.scenario_id,
    )
    await validate_data_set_versions(project_id, payload.data_set_version_ids)
    draft = {
        "_id": new_id("TCD"),
        "project_id": project_id,
        **payload.model_dump(),
        "test_case_key": payload.test_case_key or await next_key(project_id, "test_case", "TC"),
        "status": "DRAFT",
        "revision": 1,
        "created_by": user.id,
        "created_at": now(),
        "updated_at": now(),
    }
    await database.value.test_case_drafts.insert_one(draft)
    await audit(user.id, "test_case_draft_created", "TestCaseDraft", draft["_id"], project_id)
    return envelope(draft, revision=1)


@router.get("/projects/{project_id}/test-case-drafts")
async def list_test_case_drafts(
    project_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.read")
    return envelope(await database.value.test_case_drafts.find({"project_id": project_id}).sort("updated_at", -1).to_list(limit))


@router.get("/test-case-drafts/{draft_id}")
async def get_test_case_draft(draft_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(
        await get_project_entity("test_case_drafts", draft_id, user, "testcase.read")
    )


@router.get("/test-cases/{test_case_id}")
async def get_test_case(test_case_id: str, user: CurrentUser = Depends(get_current_user)):
    test_case = await get_project_entity("test_cases", test_case_id, user, "testcase.read")
    version = await database.value.test_case_versions.find_one({"_id": test_case.get("current_version_id"), "project_id": test_case["project_id"]})
    return envelope({**test_case, "current_version": version})


@router.patch("/projects/{project_id}/test-cases/{draft_id}")
@router.patch("/test-cases/{draft_id}/draft")
@router.patch("/test-case-drafts/{draft_id}")
async def update_test_case_draft(
    draft_id: str,
    payload: CaseDraftPatch,
    project_id: str | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    draft = await get_project_entity(
        "test_case_drafts", draft_id, user, "testcase.update"
    )
    if project_id is not None and draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if draft["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "IMMUTABLE_TEST_CASE_DRAFT"})
    if payload.attachments is not None:
        await get_project(draft["project_id"], user, "attachment.manage")
    await validate_design_sources(
        draft["project_id"],
        payload.requirement_version_ids if payload.requirement_version_ids is not None else draft.get("requirement_version_ids", []),
        payload.acceptance_criterion_ids if payload.acceptance_criterion_ids is not None else draft.get("acceptance_criterion_ids", []),
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
    return envelope(updated, revision=updated["revision"])


@router.post("/projects/{project_id}/test-cases/{draft_id}/lint")
@router.post("/test-cases/{draft_id}/lint")
@router.post("/test-case-drafts/{draft_id}/lint")
async def lint_test_case_draft(draft_id: str, project_id: str | None = None, user: CurrentUser = Depends(get_current_user)):
    draft = await get_project_entity(
        "test_case_drafts", draft_id, user, "testcase.lint"
    )
    await get_project(draft["project_id"], user, "ai.run_lint")
    if project_id is not None and draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    findings = lint_test_case(draft)
    result = {
        "test_case_draft_id": draft_id,
        "findings": findings,
        "valid": not any(item["severity"] == "error" for item in findings),
        "model": model_metadata("test-quality-linter-v1"),
    }
    await database.value.ai_findings.insert_one({"_id": new_id("AIF"), "project_id": draft["project_id"], "artifact_type": "test_case_draft", "artifact_id": draft_id, **result, "created_at": now()})
    return envelope(result)


@router.post("/projects/{project_id}/test-cases/{draft_id}/submit-review")
async def submit_test_case_review(
    project_id: str,
    draft_id: str,
    payload: ReviewTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    draft = await get_project_entity(
        "test_case_drafts", draft_id, user, "testcase.submit_review"
    )
    if draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if draft["status"] == "IN_REVIEW":
        return envelope(draft, revision=draft["revision"])
    if draft["status"] != "DRAFT":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    if draft["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": draft["revision"]})
    findings = lint_test_case(draft)
    if any(item["severity"] == "error" for item in findings):
        raise HTTPException(status_code=409, detail={"code": "TEST_CASE_LINT_BLOCKED", "findings": findings})
    timestamp = now()
    result = await database.value.test_case_drafts.update_one(
        {"_id": draft_id, "project_id": project_id, "revision": payload.expected_revision, "status": "DRAFT"},
        {
            "$set": {
                "status": "IN_REVIEW",
                "review_note": payload.review_note,
                "review_submitted_by": user.id,
                "review_submitted_at": timestamp,
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
    )
    if result.matched_count != 1:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    draft = await database.value.test_case_drafts.find_one({"_id": draft_id, "project_id": project_id})
    await audit(user.id, "test_case_review_submitted", "TestCaseDraft", draft_id, project_id, {"review_note": payload.review_note})
    return envelope(draft, revision=draft["revision"])


@router.post("/test-cases/{draft_id}/review")
async def submit_test_case_review_alias(
    draft_id: str,
    payload: ReviewTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    draft = await get_project_entity("test_case_drafts", draft_id, user, "testcase.submit_review")
    return await submit_test_case_review(draft["project_id"], draft_id, payload, user)


@router.post("/projects/{project_id}/test-cases/{draft_id}/request-changes")
async def request_test_case_changes(
    project_id: str,
    draft_id: str,
    payload: ReviewTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    draft = await get_project_entity(
        "test_case_drafts", draft_id, user, "testcase.review"
    )
    await require_action_policy(draft["project_id"], user, "testcase.request_changes", {"QA_LEAD"})
    if draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    if draft["status"] != "IN_REVIEW":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    if draft["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": draft["revision"]})
    timestamp = now()
    result = await database.value.test_case_drafts.update_one(
        {"_id": draft_id, "project_id": project_id, "revision": payload.expected_revision, "status": "IN_REVIEW"},
        {
            "$set": {
                "status": "DRAFT",
                "review_note": payload.review_note,
                "changes_requested_by": user.id,
                "changes_requested_at": timestamp,
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
    )
    if result.matched_count != 1:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    draft = await database.value.test_case_drafts.find_one({"_id": draft_id, "project_id": project_id})
    await audit(user.id, "test_case_changes_requested", "TestCaseDraft", draft_id, project_id, {"review_note": payload.review_note})
    return envelope(draft, revision=draft["revision"])


@router.post("/test-case-drafts/{draft_id}/freeze", status_code=201)
async def freeze_test_case_draft(
    draft_id: str,
    payload: CaseFreezeInput,
    user: CurrentUser = Depends(get_current_user),
):
    draft = await get_project_entity(
        "test_case_drafts", draft_id, user, "testcase.approve"
    )
    if draft["status"] == "APPROVED" and draft.get("frozen_version_id"):
        version = await database.value.test_case_versions.find_one(
            {"_id": draft["frozen_version_id"], "project_id": draft["project_id"]}
        )
        test_case = await database.value.test_cases.find_one(
            {"_id": version["test_case_id"], "project_id": draft["project_id"]}
        )
        return envelope({"test_case": test_case, "version": version})
    if draft["status"] != "IN_REVIEW":
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    if draft["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": draft["revision"]})
    findings = lint_test_case(draft)
    if any(item["severity"] == "error" for item in findings):
        raise HTTPException(status_code=409, detail={"code": "TEST_CASE_LINT_BLOCKED", "findings": findings})
    claimed = await database.value.test_case_drafts.find_one_and_update(
        {"_id": draft_id, "project_id": draft["project_id"], "status": "IN_REVIEW", "revision": payload.expected_revision},
        {"$set": {"status": "APPROVING", "approval_started_by": user.id, "approval_started_at": now(), "updated_at": now()}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not claimed:
        current = await database.value.test_case_drafts.find_one({"_id": draft_id, "project_id": draft["project_id"]})
        if current and current.get("status") == "APPROVED" and current.get("frozen_version_id"):
            version = await database.value.test_case_versions.find_one({"_id": current["frozen_version_id"], "project_id": current["project_id"]})
            test_case = await database.value.test_cases.find_one({"_id": version["test_case_id"], "project_id": current["project_id"]})
            return envelope({"test_case": test_case, "version": version})
        raise HTTPException(status_code=409, detail={"code": "TEST_CASE_APPROVAL_IN_PROGRESS"})
    draft = claimed
    timestamp = now()
    test_case = None
    version = None
    parent_version_id = None
    created_test_case = False
    try:
        existing = await database.value.test_cases.find_one({"project_id": draft["project_id"], "test_case_key": draft["test_case_key"]})
        if existing:
            latest = await database.value.test_case_versions.find_one({"test_case_id": existing["_id"]}, sort=[("version", -1)])
            if not latest:
                raise HTTPException(status_code=409, detail={"code": "TEST_CASE_VERSION_HISTORY_INVALID"})
            test_case = existing
            version_number = int(latest["version"]) + 1
            parent_version_id = latest["_id"]
        else:
            test_case = {
                "_id": new_id("TC"),
                "project_id": draft["project_id"],
                "test_case_key": draft["test_case_key"],
                "current_version_id": None,
                "status": "ACTIVE",
                "owner_id": draft.get("owner_id") or draft.get("created_by"),
                "tags": draft.get("tags", []),
                "created_at": timestamp,
                "updated_at": timestamp,
            }
            await database.value.test_cases.insert_one(test_case)
            created_test_case = True
            version_number = 1
        version = {
            "_id": new_id("TCV"),
            "project_id": draft["project_id"],
            "test_case_id": test_case["_id"],
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
            "status": "ACTIVE",
            "approved_by": user.id,
            "created_at": timestamp,
        }
        await database.value.test_case_versions.insert_one(version)
        updated_case = await database.value.test_cases.update_one(
            {"_id": test_case["_id"], "project_id": draft["project_id"], "current_version_id": parent_version_id},
            {"$set": {"current_version_id": version["_id"], "status": "ACTIVE", "updated_at": timestamp}},
        )
        if updated_case.matched_count != 1:
            raise HTTPException(status_code=409, detail={"code": "TEST_CASE_VERSION_CONFLICT"})
        updated_draft = await database.value.test_case_drafts.update_one(
            {"_id": draft_id, "project_id": draft["project_id"], "status": "APPROVING", "revision": draft["revision"]},
            {"$set": {"status": "APPROVED", "frozen_version_id": version["_id"], "updated_at": timestamp}, "$inc": {"revision": 1}},
        )
        if updated_draft.matched_count != 1:
            raise HTTPException(status_code=409, detail={"code": "TEST_CASE_APPROVAL_CONFLICT"})
    except Exception:
        if version:
            await database.value.test_case_versions.delete_one({"_id": version["_id"], "project_id": draft["project_id"]})
        if test_case and created_test_case:
            await database.value.test_cases.delete_one({"_id": test_case["_id"], "project_id": draft["project_id"], "current_version_id": {"$in": [None, version["_id"] if version else None]}})
        elif test_case and version:
            await database.value.test_cases.update_one({"_id": test_case["_id"], "project_id": draft["project_id"], "current_version_id": version["_id"]}, {"$set": {"current_version_id": parent_version_id, "updated_at": now()}})
        await database.value.test_case_drafts.update_one(
            {"_id": draft_id, "project_id": draft["project_id"], "status": "APPROVING"},
            {"$set": {"status": "IN_REVIEW", "approval_error_at": now(), "updated_at": now()}},
        )
        raise
    trace_ready = True
    try:
        await create_suggested_traces(draft, version, user)
    except Exception:
        trace_ready = False
    indexed = await index_artifact(version["project_id"], "test_case_version", version["test_case_id"], version["_id"], version["title"], version["plain_text_projection"], version["status"], "approved", version["version"])
    await audit(user.id, "test_case_version_approved", "TestCaseVersion", version["_id"], draft["project_id"], {"draft_id": draft_id})
    ready = trace_ready and indexed
    return envelope({"test_case": {**test_case, "current_version_id": version["_id"]}, "version": version}, status="SUCCESS" if ready else "DEGRADED", degraded_mode=None if ready else "DEGRADED_DERIVED_DATA")


@router.post("/projects/{project_id}/test-cases/{draft_id}/approve", status_code=201)
async def approve_test_case(
    project_id: str,
    draft_id: str,
    payload: CaseFreezeInput,
    user: CurrentUser = Depends(get_current_user),
):
    draft = await get_project_entity(
        "test_case_drafts", draft_id, user, "testcase.approve"
    )
    if draft["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    return await freeze_test_case_draft(draft_id, payload, user)


@router.post("/test-cases/{draft_id}/approve", status_code=201)
async def approve_test_case_alias(
    draft_id: str,
    payload: CaseFreezeInput,
    user: CurrentUser = Depends(get_current_user),
):
    draft = await get_project_entity("test_case_drafts", draft_id, user, "testcase.approve")
    return await freeze_test_case_draft(draft_id, payload, user)


@router.get("/projects/{project_id}/test-cases")
async def list_test_cases(
    project_id: str,
    q: str = Query(default="", max_length=300),
    key: str = Query(default="", max_length=80),
    title: str = Query(default="", max_length=300),
    status: str = Query(default="", max_length=30),
    priority: str = Query(default="", max_length=30),
    test_type: str = Query(default="", max_length=40),
    technique: str = Query(default="", max_length=80),
    stale_status: str = Query(default="", max_length=30),
    automation_status: str = Query(default="", max_length=30),
    requirement_id: str = Query(default="", max_length=200),
    suite_id: str = Query(default="", max_length=200),
    latest_result: str = Query(default="", max_length=30),
    tag: str = Query(default="", max_length=100),
    owner: str = Query(default="", max_length=200),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    sort: str = Query(default="-updated_at", max_length=80),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user, "testcase.read")
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    tests = await database.value.test_cases.find(query).to_list(20000)
    version_ids = [item["current_version_id"] for item in tests if item.get("current_version_id")]
    versions = await database.value.test_case_versions.find(
        {"project_id": project_id, "_id": {"$in": version_ids}}
    ).to_list(20000)
    by_id = {item["_id"]: item for item in versions}
    items = [{**item, "current_version": by_id.get(item.get("current_version_id"))} for item in tests]
    traces = await database.value.trace_links.find(
        {
            "project_id": project_id,
            "target_id": {"$in": version_ids},
            "status": "CONFIRMED",
        },
        {"target_id": 1},
    ).to_list(50000)
    trace_counts = {}
    for trace in traces:
        trace_counts[trace["target_id"]] = trace_counts.get(trace["target_id"], 0) + 1
    results = await database.value.test_results.find(
        {"project_id": project_id, "test_case_version_id": {"$in": version_ids}}
    ).sort("updated_at", -1).to_list(50000)
    latest_results = {}
    for result in results:
        latest_results.setdefault(result["test_case_version_id"], result.get("status"))
    suite_version_ids = set()
    if suite_id:
        suite = await database.value.test_suites.find_one({"_id": suite_id, "project_id": project_id})
        if not suite:
            raise HTTPException(status_code=422, detail={"code": "INVALID_TEST_SUITE"})
        suite_version_ids = set(suite.get("test_case_version_ids", []))
    requirement_version_ids = set()
    if requirement_id:
        requirement_version_ids = {
            item["_id"]
            for item in await database.value.requirement_versions.find(
                {"project_id": project_id, "requirement_id": requirement_id}, {"_id": 1}
            ).to_list(1000)
        }
        requirement_version_ids.add(requirement_id)
    for item in items:
        version = item.get("current_version") or {}
        version_id = item.get("current_version_id")
        item["trace_count"] = trace_counts.get(version_id, 0)
        item["latest_result"] = latest_results.get(version_id)
        item["stale_status"] = version.get("stale_status") or (
            "STALE" if item.get("status") == "NEEDS_UPDATE" else "FRESH"
        )
        item["owner_id"] = version.get("owner_id")
        item["tags"] = sorted(set(item.get("tags", [])) | set(version.get("tags", [])))
    terms = [value.strip().lower() for value in (q, key, title) if value.strip()]
    if terms:
        def matches_test_case(item):
            version = item.get("current_version") or {}
            searchable = f"{item.get('test_case_key', '')} {version.get('title', '')}".lower()
            return all(value in searchable for value in terms)
        items = [item for item in items if matches_test_case(item)]
    field_filters = {
        "priority": priority,
        "type": test_type,
        "automation_status": automation_status,
        "owner_id": owner,
    }
    for field, value in field_filters.items():
        if value:
            items = [
                item
                for item in items
                if (item.get("current_version") or {}).get(field, item.get(field)) == value
            ]
    if technique:
        items = [item for item in items if technique in (item.get("current_version") or {}).get("techniques", [])]
    if tag:
        items = [item for item in items if tag in item.get("tags", [])]
    if stale_status:
        items = [item for item in items if item.get("stale_status") == stale_status]
    if latest_result:
        items = [item for item in items if item.get("latest_result") == latest_result]
    if requirement_id:
        items = [
            item
            for item in items
            if requirement_version_ids
            & set((item.get("current_version") or {}).get("requirement_version_ids", []))
        ]
    if suite_id:
        items = [item for item in items if item.get("current_version_id") in suite_version_ids]
    sort_field, direction = sort_spec(
        sort,
        {
            "test_case_key",
            "status",
            "updated_at",
            "created_at",
            "title",
            "priority",
            "stale_status",
            "latest_result",
        },
    )
    items.sort(
        key=lambda item: str(
            (item.get("current_version") or {}).get(sort_field, item.get(sort_field, "")) or ""
        ).lower(),
        reverse=direction < 0,
    )
    total = len(items)
    start = (page - 1) * page_size
    return envelope(page_payload(items[start : start + page_size], page, page_size, total))


@router.post("/test-cases/{test_case_id}/clone", status_code=201)
async def clone_test_case(
    test_case_id: str,
    payload: TestCaseCloneInput,
    user: CurrentUser = Depends(get_current_user),
):
    test_case = await get_project_entity("test_cases", test_case_id, user, "testcase.clone")
    if test_case.get("current_version_id") != payload.expected_current_version_id:
        raise HTTPException(
            status_code=409,
            detail={
                "code": "REVISION_CONFLICT",
                "current_version_id": test_case.get("current_version_id"),
            },
        )
    version = await database.value.test_case_versions.find_one(
        {
            "_id": payload.expected_current_version_id,
            "project_id": test_case["project_id"],
            "test_case_id": test_case_id,
        }
    )
    if not version:
        raise HTTPException(status_code=422, detail={"code": "TEST_CASE_VERSION_NOT_FOUND"})
    source_evidence = list(version.get("source_evidence", []))
    source_evidence.append(
        {
            "artifact_type": "test_case_version",
            "artifact_id": test_case_id,
            "artifact_version_id": version["_id"],
            "relation": "cloned_from",
        }
    )
    result = await create_test_case_draft(
        test_case["project_id"],
        CaseDraftCreate(
            title=payload.title or f"{version['title']} bản sao",
            type=version["type"],
            priority=version["priority"],
            risk=version["risk"],
            objective_doc=version.get("objective_doc", {"type": "doc", "content": []}),
            preconditions_doc=version["preconditions_doc"],
            steps=version["steps"],
            test_data=version["test_data"],
            expected_result_doc=version["expected_result_doc"],
            postconditions_doc=version["postconditions_doc"],
            tags=version.get("tags", []),
            techniques=version.get("techniques", []),
            automation_status=version.get("automation_status", "manual"),
            attachments=version.get("attachments", []),
            data_set_version_ids=version.get("data_set_version_ids", []),
            requirement_version_ids=version.get("requirement_version_ids", []),
            acceptance_criterion_ids=version.get("acceptance_criterion_ids", []),
            scenario_id=version.get("scenario_id"),
            origin="clone",
            source_evidence=source_evidence,
        ),
        user,
    )
    await audit(
        user.id,
        "test_case_cloned",
        "TestCaseDraft",
        result["data"]["_id"],
        test_case["project_id"],
        {"source_test_case_id": test_case_id, "source_version_id": version["_id"]},
    )
    return result


@router.get("/test-cases/{test_case_id}/versions")
async def list_test_case_versions(test_case_id: str, user: CurrentUser = Depends(get_current_user)):
    test_case = await get_project_entity(
        "test_cases", test_case_id, user, "testcase.version.read"
    )
    versions = await database.value.test_case_versions.find({"test_case_id": test_case_id}).sort("version", -1).to_list(500)
    return envelope(versions)


@router.post("/test-cases/{test_case_id}/versions/draft", status_code=201)
async def create_test_case_version_draft(
    test_case_id: str,
    payload: dict = Body(),
    user: CurrentUser = Depends(get_current_user),
):
    test_case = await get_project_entity(
        "test_cases", test_case_id, user, "testcase.version.create"
    )
    expected_version_id = str(payload.get("expected_current_version_id") or "")
    if expected_version_id != test_case.get("current_version_id"):
        raise HTTPException(
            status_code=409,
            detail={
                "code": "REVISION_CONFLICT",
                "current_version_id": test_case.get("current_version_id"),
            },
        )
    reason = str(payload.get("change_reason") or "").strip()
    if len(reason) < 2:
        raise HTTPException(status_code=422, detail={"code": "CHANGE_REASON_REQUIRED"})
    version = await database.value.test_case_versions.find_one(
        {
            "_id": expected_version_id,
            "project_id": test_case["project_id"],
            "test_case_id": test_case_id,
        }
    )
    if not version:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    result = await create_test_case_draft(
        test_case["project_id"],
        CaseDraftCreate(
            test_case_key=test_case["test_case_key"],
            title=str(payload.get("title") or version["title"]),
            type=version["type"],
            priority=version["priority"],
            risk=version["risk"],
            objective_doc=version.get("objective_doc", {"type": "doc", "content": []}),
            preconditions_doc=version["preconditions_doc"],
            steps=version["steps"],
            test_data=version["test_data"],
            expected_result_doc=version["expected_result_doc"],
            postconditions_doc=version["postconditions_doc"],
            tags=version.get("tags", []),
            techniques=version.get("techniques", []),
            automation_status=version.get("automation_status", "manual"),
            attachments=version.get("attachments", []),
            data_set_version_ids=version.get("data_set_version_ids", []),
            requirement_version_ids=version.get("requirement_version_ids", []),
            acceptance_criterion_ids=version.get("acceptance_criterion_ids", []),
            scenario_id=version.get("scenario_id"),
            origin="manual",
            source_evidence=[
                *version.get("source_evidence", []),
                {
                    "artifact_type": "test_case_version",
                    "artifact_id": test_case_id,
                    "artifact_version_id": version["_id"],
                    "relation": "new_version_from",
                },
            ],
        ),
        user,
    )
    await database.value.test_case_drafts.update_one(
        {"_id": result["data"]["_id"]},
        {"$set": {"change_reason": reason, "parent_version_id": version["_id"]}},
    )
    result["data"]["change_reason"] = reason
    result["data"]["parent_version_id"] = version["_id"]
    return result


@router.get("/test-cases/{test_case_id}/diff")
async def diff_test_case_versions(
    test_case_id: str,
    from_version: str = Query(alias="from", min_length=1, max_length=200),
    to_version: str = Query(alias="to", min_length=1, max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    test_case = await get_project_entity(
        "test_cases", test_case_id, user, "testcase.version.read"
    )
    versions = await database.value.test_case_versions.find(
        {
            "_id": {"$in": [from_version, to_version]},
            "project_id": test_case["project_id"],
            "test_case_id": test_case_id,
        }
    ).to_list(2)
    by_id = {item["_id"]: item for item in versions}
    if from_version not in by_id or to_version not in by_id:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    before = by_id[from_version]
    after = by_id[to_version]
    fields = [
        "title",
        "type",
        "priority",
        "risk",
        "objective_doc",
        "preconditions_doc",
        "steps",
        "test_data",
        "expected_result_doc",
        "postconditions_doc",
        "tags",
        "techniques",
        "automation_status",
        "requirement_version_ids",
        "acceptance_criterion_ids",
    ]
    changes = [
        {"field": field, "before": before.get(field), "after": after.get(field)}
        for field in fields
        if before.get(field) != after.get(field)
    ]
    return envelope(
        {
            "test_case_id": test_case_id,
            "from_version_id": from_version,
            "to_version_id": to_version,
            "changes": changes,
        }
    )


@router.post("/test-cases/{test_case_id}/obsolete")
async def mark_test_case_obsolete(
    test_case_id: str,
    payload: dict = Body(),
    user: CurrentUser = Depends(get_current_user),
):
    test_case = await get_project_entity(
        "test_cases", test_case_id, user, "testcase.archive"
    )
    if test_case.get("status") == "OBSOLETE":
        return envelope(test_case)
    if test_case.get("status") not in {"ACTIVE", "NEEDS_UPDATE"}:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION"})
    if payload.get("expected_current_version_id") != test_case.get("current_version_id"):
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_version_id": test_case.get("current_version_id")})
    reason = str(payload.get("reason") or "").strip()
    if len(reason) < 2:
        raise HTTPException(status_code=422, detail={"code": "OBSOLETE_REASON_REQUIRED"})
    await database.value.test_cases.update_one({"_id": test_case_id}, {"$set": {"status": "OBSOLETE", "obsolete_reason": reason, "obsolete_by": user.id, "obsolete_at": now(), "updated_at": now()}})
    await audit(user.id, "test_case_marked_obsolete", "TestCase", test_case_id, test_case["project_id"], {"reason": reason})
    return envelope(await database.value.test_cases.find_one({"_id": test_case_id}))


@router.post("/test-cases/{test_case_id}/restore")
async def restore_test_case(
    test_case_id: str,
    payload: dict = Body(),
    user: CurrentUser = Depends(get_current_user),
):
    test_case = await get_project_entity(
        "test_cases", test_case_id, user, "testcase.restore"
    )
    if test_case.get("status") != "OBSOLETE":
        return envelope(test_case)
    if payload.get("expected_current_version_id") != test_case.get("current_version_id"):
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    reason = str(payload.get("reason") or "").strip()
    if len(reason) < 2:
        raise HTTPException(status_code=422, detail={"code": "RESTORE_REASON_REQUIRED"})
    await database.value.test_cases.update_one(
        {"_id": test_case_id, "project_id": test_case["project_id"]},
        {
            "$set": {
                "status": "ACTIVE",
                "restore_reason": reason,
                "restored_by": user.id,
                "restored_at": now(),
                "updated_at": now(),
            }
        },
    )
    await audit(
        user.id,
        "test_case_restored",
        "TestCase",
        test_case_id,
        test_case["project_id"],
        {"reason": reason},
    )
    return envelope(await database.value.test_cases.find_one({"_id": test_case_id}))


@router.post("/requirement-versions/{version_id}/ai/generate-test-cases", status_code=201)
async def generate_test_cases(
    version_id: str,
    payload: GenerateInput,
    user: CurrentUser = Depends(get_current_user),
):
    with AI_GENERATION_LATENCY.labels("test_case").time():
        version = await get_project_entity(
            "requirement_versions", version_id, user, "ai.generate_testcase"
        )
        criteria = await database.value.acceptance_criteria.find({"requirement_version_id": version_id}).to_list(500)
        categories = payload.categories or ["happy_path", "negative", "boundary"]
        created = []
        for category in categories:
            for number in range(payload.count_per_category):
                criterion = criteria[number % len(criteria)] if criteria else None
                evidence_text = criterion.get("plain_text") if criterion else version["plain_text_projection"]
                draft_payload = CaseDraftCreate(
                    title=f"{category.replace('_', ' ').title()} cho {version['title']}",
                    type=category,
                    priority=version.get("priority", "medium"),
                    risk=version.get("risk", "medium"),
                    objective_doc=text_doc(evidence_text),
                    preconditions_doc=text_doc(f"Requirement {version['requirement_key']} đã sẵn sàng để kiểm thử"),
                    steps=[
                        {"id": "step-1", "order": 1, "action_doc": text_doc(f"Thực hiện hành vi theo {evidence_text}"), "test_data": {}, "expected_doc": text_doc("Hệ thống phản hồi đúng theo baseline")}
                    ],
                    test_data={"source": "baseline"},
                    expected_result_doc=text_doc(evidence_text),
                    techniques=techniques_for_category(category),
                    requirement_version_ids=[version_id],
                    acceptance_criterion_ids=[criterion["_id"]] if criterion else [],
                    origin="ai_generated",
                    source_evidence=[{"artifact_type": "acceptance_criterion" if criterion else "requirement_version", "artifact_version_id": criterion["_id"] if criterion else version_id, "text": evidence_text}],
                )
                response = await create_test_case_draft(version["project_id"], draft_payload, user)
                created.append(response["data"])
    await audit(user.id, "test_case_drafts_generated", "RequirementVersion", version_id, version["project_id"], {"count": len(created)})
    return envelope({"items": created, "evidence": criteria, "model": model_metadata("test-generator-v1")})


@router.post("/projects/{project_id}/test-cases/generate", status_code=201)
async def generate_project_test_cases(
    project_id: str,
    payload: TestCaseGenerateInput,
    user: CurrentUser = Depends(get_current_user),
):
    version = await get_project_entity("requirement_versions", payload.requirement_version_id, user, "ai.generate_testcase")
    if version["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": "PROJECT_MISMATCH"})
    return await generate_test_cases(payload.requirement_version_id, GenerateInput(categories=payload.categories, count_per_category=payload.count_per_category, instruction=payload.instruction), user)


@router.get("/projects/{project_id}/test-cases/duplicates")
async def find_duplicates(project_id: str, user: CurrentUser = Depends(get_current_user)):
    await get_project(project_id, user, "testcase.duplicate_check")
    await get_project(project_id, user, "ai.run_duplicate_check")
    versions = await database.value.test_case_versions.find({"project_id": project_id, "status": "ACTIVE"}).to_list(2000)
    pairs = []
    for index, left in enumerate(versions):
        for right in versions[index + 1 :]:
            score, reasons = duplicate_score(left, right)
            if score >= 0.72:
                pairs.append({"left": left, "right": right, "similarity": score, "reasons": reasons})
    return envelope(sorted(pairs, key=lambda item: item["similarity"], reverse=True)[:100])


async def create_suggested_traces(draft, version, user):
    sources = [
        ("requirement_version", source_id)
        for source_id in draft.get("requirement_version_ids", [])
    ] + [
        ("acceptance_criterion", source_id)
        for source_id in draft.get("acceptance_criterion_ids", [])
    ]
    for source_type, source_id in sources:
        exists = await database.value.trace_links.find_one({"project_id": draft["project_id"], "source_type": source_type, "source_id": source_id, "target_type": "test_case_version", "target_id": version["_id"]})
        if exists:
            continue
        await database.value.trace_links.insert_one(
            {
                "_id": new_id("TL"),
                "project_id": draft["project_id"],
                "source_type": source_type,
                "source_id": source_id,
                "target_type": "test_case_version",
                "target_id": version["_id"],
                "link_type": "verifies",
                "confidence": 0.9 if draft.get("origin") == "ai_generated" else 1,
                "origin": "ai_suggested" if draft.get("origin") == "ai_generated" else "manual",
                "status": "SUGGESTED" if draft.get("origin") == "ai_generated" else "CONFIRMED",
                "revision": 1,
                "evidence": draft.get("source_evidence", []),
                "created_by": user.id,
                "created_at": now(),
            }
        )


def project_test_text(value):
    steps = " ".join(
        f"{plain_text(step.get('action_doc', {}))} {plain_text(step.get('expected_doc', {}))}"
        for step in value.get("steps", [])
    )
    return " ".join([value.get("title", ""), plain_text(value.get("objective_doc", {})), plain_text(value.get("preconditions_doc", {})), steps, plain_text(value.get("expected_result_doc", {}))]).strip()


def techniques_for_category(category):
    return {
        "boundary": ["boundary_value", "equivalence_partitioning"],
        "permission": ["permission_matrix"],
        "state_transition": ["state_transition"],
        "api": ["contract", "negative_testing"],
        "negative": ["negative_testing"],
        "validation": ["equivalence_partitioning"],
    }.get(category, ["functional"])


async def validate_design_sources(project_id, requirement_version_ids, acceptance_criterion_ids, scenario_id=None):
    requirement_ids = list(dict.fromkeys(requirement_version_ids or []))
    criterion_ids = list(dict.fromkeys(acceptance_criterion_ids or []))
    if requirement_ids:
        count = await database.value.requirement_versions.count_documents({"project_id": project_id, "_id": {"$in": requirement_ids}})
        if count != len(requirement_ids):
            raise HTTPException(status_code=422, detail={"code": "CROSS_PROJECT_OR_MISSING_REQUIREMENT_VERSION"})
    if criterion_ids:
        query = {"project_id": project_id, "_id": {"$in": criterion_ids}}
        if requirement_ids:
            query["requirement_version_id"] = {"$in": requirement_ids}
        count = await database.value.acceptance_criteria.count_documents(query)
        if count != len(criterion_ids):
            raise HTTPException(status_code=422, detail={"code": "CROSS_PROJECT_OR_MISSING_ACCEPTANCE_CRITERION"})
    if scenario_id:
        scenario = await database.value.test_scenarios.find_one({"_id": scenario_id, "project_id": project_id})
        if not scenario:
            raise HTTPException(status_code=422, detail={"code": "CROSS_PROJECT_OR_MISSING_TEST_SCENARIO"})


async def validate_data_set_versions(project_id, data_set_version_ids):
    version_ids = list(dict.fromkeys(data_set_version_ids or []))
    if not version_ids:
        return
    count = await database.value.data_set_versions.count_documents(
        {"project_id": project_id, "_id": {"$in": version_ids}}
    )
    if count != len(version_ids):
        raise HTTPException(
            status_code=422,
            detail={"code": "CROSS_PROJECT_OR_MISSING_DATA_SET_VERSION"},
        )


def text_doc(value):
    return {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": str(value)}]}]}


def model_metadata(model):
    return {
        "provider": "deterministic",
        "model": model,
        "prompt_version": "qa-v1",
        "tool_schema_version": "1",
        "retrieval_version": "project-filter-v1",
    }
