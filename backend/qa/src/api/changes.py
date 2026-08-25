from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import audit, envelope, get_project, get_project_entity, new_id, now
from src.core.database import database
from src.core.metrics import PROPOSAL_ACCEPTANCE_RATE
from src.domain.schemas import ProposalAction, RequirementCompareInput
from src.services.change_analysis import classify_test_impact, semantic_changes
from src.services.project_rag import index_artifact


router = APIRouter(prefix="/api/qa", tags=["QA Change Maintenance"])


@router.post("/requirements/{requirement_id}/change-sets", status_code=201)
async def create_change_set(
    requirement_id: str,
    payload: RequirementCompareInput,
    user: CurrentUser = Depends(get_current_user),
):
    requirement = await get_project_entity("requirements", requirement_id, user, write=True)
    versions = await database.value.requirement_versions.find({"requirement_id": requirement_id, "_id": {"$in": [payload.from_version_id, payload.to_version_id]}}).to_list(2)
    by_id = {item["_id"]: item for item in versions}
    if set(by_id) != {payload.from_version_id, payload.to_version_id}:
        raise HTTPException(status_code=422, detail={"code": "INVALID_REQUIREMENT_VERSION_PAIR"})
    if by_id[payload.to_version_id].get("status") != "BASELINED":
        raise HTTPException(status_code=409, detail={"code": "TARGET_VERSION_NOT_BASELINED"})
    existing = await database.value.requirement_change_sets.find_one({"requirement_id": requirement_id, "to_version_id": payload.to_version_id})
    if existing:
        return envelope(existing)
    changes = semantic_changes(by_id[payload.from_version_id], by_id[payload.to_version_id])
    change_set = {
        "_id": new_id("CHG"),
        "project_id": requirement["project_id"],
        "requirement_id": requirement_id,
        "from_version_id": payload.from_version_id,
        "to_version_id": payload.to_version_id,
        "changes": changes,
        "model_version": "semantic-diff-v1",
        "status": "READY",
        "created_by": user.id,
        "created_at": now(),
    }
    await database.value.requirement_change_sets.insert_one(change_set)
    await mark_previous_traces_stale(change_set)
    await audit(user.id, "requirement_change_set_created", "RequirementChangeSet", change_set["_id"], requirement["project_id"], {"change_count": len(changes)})
    return envelope(change_set)


@router.get("/projects/{project_id}/change-sets")
async def list_change_sets(
    project_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user)
    return envelope(await database.value.requirement_change_sets.find({"project_id": project_id}).sort("created_at", -1).to_list(limit))


@router.get("/change-sets/{change_set_id}")
async def get_change_set(change_set_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await get_project_entity("requirement_change_sets", change_set_id, user))


@router.post("/change-sets/{change_set_id}/impact-analysis", status_code=201)
async def analyze_impact(change_set_id: str, user: CurrentUser = Depends(get_current_user)):
    change_set = await get_project_entity("requirement_change_sets", change_set_id, user, write=True)
    existing = await database.value.impact_analyses.find_one({"change_set_id": change_set_id, "model_version": "agentic-hybrid-v1"})
    if existing:
        return envelope(existing)
    criteria = await database.value.acceptance_criteria.find(
        {
            "requirement_version_id": {
                "$in": [change_set["from_version_id"], change_set["to_version_id"]]
            }
        }
    ).to_list(10000)
    source_ids = {change_set["from_version_id"], change_set["to_version_id"], *[item["_id"] for item in criteria]}
    links = await database.value.trace_links.find({"project_id": change_set["project_id"], "source_id": {"$in": list(source_ids)}, "status": {"$in": ["CONFIRMED", "STALE"]}}).to_list(50000)
    direct_targets = {link["target_id"] for link in links}
    current_tests = await database.value.test_cases.find({"project_id": change_set["project_id"], "status": {"$in": ["ACTIVE", "NEEDS_UPDATE"]}}).to_list(20000)
    versions = await database.value.test_case_versions.find({"_id": {"$in": [item["current_version_id"] for item in current_tests if item.get("current_version_id")]}}).to_list(20000)
    impacted = [classify_test_impact(version, change_set["changes"], version["_id"] in direct_targets) for version in versions]
    affected = [item for item in impacted if item["classification"] != "STILL_VALID" or item["test_case_version_id"] in direct_targets]
    new_test_requirements = []
    if any(change["type"] in {"ADDED_BEHAVIOR", "MODIFIED_BOUNDARY", "MODIFIED_PERMISSION", "MODIFIED_ERROR"} for change in change_set["changes"]):
        if not any(item["classification"] == "NEEDS_UPDATE" for item in affected):
            new_test_requirements.append({"classification": "NEW_TEST_REQUIRED", "reason": "Thay đổi hành vi chưa có Test Case trực tiếp chứng minh", "evidence": change_set["changes"]})
    analysis = {
        "_id": new_id("IMP"),
        "project_id": change_set["project_id"],
        "change_set_id": change_set_id,
        "affected_test_cases": affected,
        "new_test_requirements": new_test_requirements,
        "status": "DRAFT",
        "model_version": "agentic-hybrid-v1",
        "pipeline": ["direct_trace", "semantic_candidate", "deterministic_check", "evidence_classification"],
        "created_by": user.id,
        "created_at": now(),
    }
    await database.value.impact_analyses.insert_one(analysis)
    await audit(user.id, "impact_analysis_created", "ImpactAnalysis", analysis["_id"], change_set["project_id"], {"affected_count": len(affected)})
    return envelope(analysis)


@router.get("/impact-analyses/{analysis_id}")
async def get_impact_analysis(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await get_project_entity("impact_analyses", analysis_id, user))


@router.post("/impact-analyses/{analysis_id}/maintenance-proposals", status_code=201)
async def create_maintenance_proposals(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    analysis = await get_project_entity("impact_analyses", analysis_id, user, write=True)
    existing = await database.value.maintenance_proposals.find({"impact_analysis_id": analysis_id, "status": "PENDING"}).to_list(10000)
    if existing:
        return envelope(existing)
    proposals = []
    change_set = await database.value.requirement_change_sets.find_one({"_id": analysis["change_set_id"]})
    for item in analysis["affected_test_cases"]:
        if item["classification"] != "NEEDS_UPDATE":
            continue
        base = await database.value.test_case_versions.find_one({"_id": item["test_case_version_id"]})
        patch = proposed_patch(base, change_set["changes"])
        proposal = {
            "_id": new_id("MP"),
            "project_id": analysis["project_id"],
            "impact_analysis_id": analysis_id,
            "proposal_type": "UPDATE_TEST_CASE",
            "test_case_key": item.get("test_case_key"),
            "target_artifact_id": item["test_case_id"],
            "base_version_id": item["test_case_version_id"],
            "patch": patch,
            "reason": " · ".join(item["reasons"]),
            "evidence": item["evidence"] + change_set["changes"],
            "status": "PENDING",
            "revision": 1,
            "model_version": "maintenance-agent-v1",
            "created_by": user.id,
            "created_at": now(),
            "updated_at": now(),
        }
        proposals.append(proposal)
    for item in analysis.get("new_test_requirements", []):
        proposals.append({"_id": new_id("MP"), "project_id": analysis["project_id"], "impact_analysis_id": analysis_id, "proposal_type": "CREATE_TEST_CASE", "target_artifact_id": None, "base_version_id": None, "patch": {"title": "Test Case mới cho hành vi thay đổi", "type": "boundary", "requirement_version_ids": [change_set["to_version_id"]]}, "reason": item["reason"], "evidence": item["evidence"], "status": "PENDING", "revision": 1, "model_version": "maintenance-agent-v1", "created_by": user.id, "created_at": now(), "updated_at": now()})
    if proposals:
        await database.value.maintenance_proposals.insert_many(proposals)
    await audit(user.id, "maintenance_proposals_created", "ImpactAnalysis", analysis_id, analysis["project_id"], {"count": len(proposals)})
    return envelope(proposals)


@router.get("/projects/{project_id}/maintenance-proposals")
async def list_proposals(
    project_id: str,
    status: str = Query(default="PENDING", max_length=30),
    limit: int = Query(default=100, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    await get_project(project_id, user)
    query = {"project_id": project_id}
    if status:
        query["status"] = status
    return envelope(await database.value.maintenance_proposals.find(query).sort("created_at", -1).to_list(limit))


@router.post("/maintenance-proposals/{proposal_id}/accept", status_code=201)
async def accept_proposal(proposal_id: str, payload: ProposalAction, user: CurrentUser = Depends(get_current_user)):
    return await apply_proposal(proposal_id, payload, user, "ACCEPTED")


@router.post("/maintenance-proposals/{proposal_id}/accept-with-edit", status_code=201)
async def accept_proposal_with_edit(proposal_id: str, payload: ProposalAction, user: CurrentUser = Depends(get_current_user)):
    return await apply_proposal(proposal_id, payload, user, "EDITED_ACCEPTED")


@router.post("/maintenance-proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: str, payload: ProposalAction, user: CurrentUser = Depends(get_current_user)):
    proposal = await get_project_entity("maintenance_proposals", proposal_id, user, write=True)
    require_pending_revision(proposal, payload)
    await database.value.maintenance_proposals.update_one({"_id": proposal_id}, {"$set": {"status": "REJECTED", "review_note": payload.review_note, "reviewed_by": user.id, "reviewed_at": now(), "updated_at": now()}, "$inc": {"revision": 1}})
    await update_proposal_acceptance_rate(proposal["project_id"])
    await audit(user.id, "maintenance_proposal_rejected", "MaintenanceProposal", proposal_id, proposal["project_id"])
    return envelope(await database.value.maintenance_proposals.find_one({"_id": proposal_id}))


async def apply_proposal(proposal_id, payload, user, final_status):
    proposal = await get_project_entity("maintenance_proposals", proposal_id, user, write=True)
    require_pending_revision(proposal, payload, allow_partial=True)
    patch = {**proposal.get("patch", {}), **(payload.patch or {})}
    try:
        if proposal.get("status") == "APPLY_PARTIAL" and proposal.get("partial_version_id"):
            result = await recover_partial_proposal(proposal, user)
        elif proposal["proposal_type"] == "CREATE_TEST_CASE":
            result = await create_test_draft_from_proposal(proposal, patch, user)
        elif proposal["proposal_type"] == "UPDATE_TEST_CASE":
            result = await create_test_version_from_proposal(proposal, patch, user)
        elif proposal["proposal_type"] == "MARK_OBSOLETE":
            result = await mark_test_obsolete(proposal, user)
        else:
            raise HTTPException(status_code=422, detail={"code": "UNSUPPORTED_PROPOSAL_TYPE"})
    except HTTPException:
        raise
    except Exception as error:
        partial = await database.value.maintenance_proposals.find_one({"_id": proposal_id})
        if partial and partial.get("partial_version_id"):
            await database.value.maintenance_proposals.update_one(
                {"_id": proposal_id},
                {"$set": {"status": "APPLY_PARTIAL", "recovery_error": str(error)[:500], "updated_at": now()}, "$inc": {"revision": 1}},
            )
            raise HTTPException(status_code=503, detail={"code": "PROPOSAL_APPLY_PARTIAL", "retryable": True, "state_after_failure": "APPLY_PARTIAL", "user_action_required": True}) from error
        raise HTTPException(status_code=503, detail={"code": "PROPOSAL_APPLY_FAILED", "retryable": True, "state_after_failure": "UNCHANGED", "user_action_required": True}) from error
    await database.value.maintenance_proposals.update_one({"_id": proposal_id}, {"$set": {"status": final_status, "applied_artifact_id": result.get("_id"), "review_note": payload.review_note, "reviewed_by": user.id, "reviewed_at": now(), "updated_at": now()}, "$inc": {"revision": 1}})
    await update_proposal_acceptance_rate(proposal["project_id"])
    await audit(user.id, "maintenance_proposal_applied", "MaintenanceProposal", proposal_id, proposal["project_id"], {"result_id": result.get("_id")})
    return envelope({"proposal": await database.value.maintenance_proposals.find_one({"_id": proposal_id}), "result": result})


async def update_proposal_acceptance_rate(project_id):
    reviewed = await database.value.maintenance_proposals.count_documents({"project_id": project_id, "status": {"$in": ["ACCEPTED", "EDITED_ACCEPTED", "REJECTED"]}})
    accepted = await database.value.maintenance_proposals.count_documents({"project_id": project_id, "status": {"$in": ["ACCEPTED", "EDITED_ACCEPTED"]}})
    PROPOSAL_ACCEPTANCE_RATE.set(accepted / reviewed if reviewed else 0)


async def create_test_version_from_proposal(proposal, patch, user):
    from src.api.test_design import project_test_text

    test_case = await database.value.test_cases.find_one({"_id": proposal["target_artifact_id"], "project_id": proposal["project_id"]})
    if not test_case or test_case.get("current_version_id") != proposal["base_version_id"]:
        raise HTTPException(status_code=409, detail={"code": "STALE_PROPOSAL", "current_version_id": test_case.get("current_version_id") if test_case else None})
    base = await database.value.test_case_versions.find_one({"_id": proposal["base_version_id"]})
    allowed = {"title", "type", "priority", "risk", "preconditions_doc", "steps", "test_data", "expected_result_doc", "postconditions_doc", "tags", "automation_status", "requirement_version_ids", "acceptance_criterion_ids"}
    merged = {**base, **{key: value for key, value in patch.items() if key in allowed}}
    merged["plain_text_projection"] = project_test_text(merged)
    version = {**{key: value for key, value in merged.items() if key not in {"_id", "version", "created_at", "approved_by", "parent_version_id", "change_reason"}}, "_id": new_id("TCV"), "version": int(base["version"]) + 1, "parent_version_id": base["_id"], "change_reason": proposal["reason"], "approved_by": user.id, "created_at": now()}
    await database.value.test_case_versions.insert_one(version)
    await database.value.maintenance_proposals.update_one({"_id": proposal["_id"]}, {"$set": {"partial_version_id": version["_id"], "apply_state": "VERSION_CREATED", "updated_at": now()}})
    await database.value.test_cases.update_one({"_id": test_case["_id"]}, {"$set": {"current_version_id": version["_id"], "status": "ACTIVE", "updated_at": now()}})
    await database.value.trace_links.update_many({"project_id": proposal["project_id"], "target_id": base["_id"], "status": {"$in": ["CONFIRMED", "STALE"]}}, {"$set": {"status": "STALE", "updated_at": now()}})
    change_set = await database.value.requirement_change_sets.find_one({"_id": (await database.value.impact_analyses.find_one({"_id": proposal["impact_analysis_id"]}))["change_set_id"]})
    await database.value.trace_links.insert_one({"_id": new_id("TL"), "project_id": proposal["project_id"], "source_type": "requirement_version", "source_id": change_set["to_version_id"], "target_type": "test_case_version", "target_id": version["_id"], "link_type": "verifies", "confidence": 1, "origin": "manual", "status": "CONFIRMED", "evidence": proposal["evidence"], "created_by": user.id, "created_at": now(), "updated_at": now()})
    await index_artifact(version["project_id"], "test_case_version", version["test_case_id"], version["_id"], version["title"], version["plain_text_projection"], version["status"], "approved", version["version"])
    return version


async def recover_partial_proposal(proposal, user):
    version = await database.value.test_case_versions.find_one({"_id": proposal["partial_version_id"], "project_id": proposal["project_id"]})
    if not version:
        raise HTTPException(status_code=409, detail={"code": "PARTIAL_ARTIFACT_NOT_FOUND", "state_after_failure": "APPLY_PARTIAL"})
    test_case = await database.value.test_cases.find_one({"_id": proposal["target_artifact_id"], "project_id": proposal["project_id"]})
    if test_case and test_case.get("current_version_id") != version["_id"]:
        await database.value.test_cases.update_one({"_id": test_case["_id"]}, {"$set": {"current_version_id": version["_id"], "status": "ACTIVE", "updated_at": now()}})
    analysis = await database.value.impact_analyses.find_one({"_id": proposal["impact_analysis_id"]})
    change_set = await database.value.requirement_change_sets.find_one({"_id": analysis["change_set_id"]}) if analysis else None
    if change_set:
        trace = await database.value.trace_links.find_one({"project_id": proposal["project_id"], "source_id": change_set["to_version_id"], "target_id": version["_id"], "status": "CONFIRMED"})
        if not trace:
            await database.value.trace_links.insert_one({"_id": new_id("TL"), "project_id": proposal["project_id"], "source_type": "requirement_version", "source_id": change_set["to_version_id"], "target_type": "test_case_version", "target_id": version["_id"], "link_type": "verifies", "confidence": 1, "origin": "manual", "status": "CONFIRMED", "evidence": proposal.get("evidence", []), "created_by": user.id, "created_at": now(), "updated_at": now()})
    await index_artifact(version["project_id"], "test_case_version", version["test_case_id"], version["_id"], version["title"], version["plain_text_projection"], version["status"], "approved", version["version"])
    return version


async def create_test_draft_from_proposal(proposal, patch, user):
    from src.api.test_design import create_test_case_draft, text_doc
    from src.domain.schemas import TestCaseDraftCreate

    payload = TestCaseDraftCreate(title=patch.get("title", "Test Case từ đề xuất bảo trì"), type=patch.get("type", "custom"), preconditions_doc=text_doc("Project sẵn sàng"), steps=[{"id": "step-1", "order": 1, "action_doc": text_doc("Thực hiện hành vi mới"), "test_data": {}, "expected_doc": text_doc("Kết quả khớp Requirement baseline")}], test_data={}, expected_result_doc=text_doc("Kết quả khớp Requirement baseline"), requirement_version_ids=patch.get("requirement_version_ids", []), origin="maintenance", source_evidence=proposal["evidence"])
    response = await create_test_case_draft(proposal["project_id"], payload, user)
    return response["data"]


async def mark_test_obsolete(proposal, user):
    test_case = await database.value.test_cases.find_one({"_id": proposal["target_artifact_id"], "project_id": proposal["project_id"]})
    if not test_case or test_case.get("current_version_id") != proposal["base_version_id"]:
        raise HTTPException(status_code=409, detail={"code": "STALE_PROPOSAL"})
    await database.value.test_cases.update_one({"_id": test_case["_id"]}, {"$set": {"status": "OBSOLETE", "updated_at": now()}})
    return await database.value.test_cases.find_one({"_id": test_case["_id"]})


@router.post("/change-sets/{change_set_id}/regression-recommendation", status_code=201)
async def regression_recommendation(change_set_id: str, user: CurrentUser = Depends(get_current_user)):
    change_set = await get_project_entity("requirement_change_sets", change_set_id, user, write=True)
    existing = await database.value.regression_recommendations.find_one({"change_set_id": change_set_id})
    if existing:
        return envelope(existing)
    analysis = await database.value.impact_analyses.find_one({"change_set_id": change_set_id}, sort=[("created_at", -1)])
    if not analysis:
        raise HTTPException(status_code=409, detail={"code": "IMPACT_ANALYSIS_REQUIRED"})
    recent_failures = await recent_failure_versions(change_set["project_id"])
    items = []
    for impact in analysis["affected_test_cases"]:
        test_case = await database.value.test_cases.find_one({"_id": impact["test_case_id"], "project_id": change_set["project_id"]})
        current_version_id = test_case.get("current_version_id") if test_case else impact["test_case_version_id"]
        direct_trace = any(item.get("direct_trace") for item in impact.get("evidence", []))
        level = "MUST_RUN" if direct_trace or impact["classification"] == "NEEDS_UPDATE" or current_version_id in recent_failures else "SHOULD_RUN" if impact["classification"] == "POTENTIALLY_AFFECTED" else "OPTIONAL"
        reasons = list(impact["reasons"])
        if current_version_id in recent_failures:
            reasons.append("Test Case có kết quả FAIL gần đây")
        items.append({"test_case_id": impact["test_case_id"], "test_case_version_id": current_version_id, "test_case_key": impact.get("test_case_key"), "level": level, "reasons": reasons, "evidence": impact["evidence"]})
    recommendation = {"_id": new_id("REG"), "project_id": change_set["project_id"], "change_set_id": change_set_id, "items": items, "model_version": "risk-score-v1", "created_by": user.id, "created_at": now()}
    await database.value.regression_recommendations.insert_one(recommendation)
    await audit(user.id, "regression_recommendation_created", "RegressionRecommendation", recommendation["_id"], change_set["project_id"])
    return envelope(recommendation)


async def recent_failure_versions(project_id):
    runs = await database.value.test_runs.find({"project_id": project_id}).sort("created_at", -1).to_list(20)
    results = await database.value.test_results.find({"test_run_id": {"$in": [item["_id"] for item in runs]}, "status": "FAIL"}).to_list(10000)
    return {item["test_case_version_id"] for item in results}


async def mark_previous_traces_stale(change_set):
    criteria = await database.value.acceptance_criteria.find({"requirement_version_id": change_set["from_version_id"]}).to_list(10000)
    await database.value.trace_links.update_many({"project_id": change_set["project_id"], "source_id": {"$in": [change_set["from_version_id"], *[item["_id"] for item in criteria]]}, "status": "CONFIRMED"}, {"$set": {"status": "STALE", "updated_at": now()}})


def proposed_patch(base, changes):
    patch = {}
    boundary = next((item for item in changes if item["type"] == "MODIFIED_BOUNDARY"), None)
    if boundary:
        values = boundary.get("after", {}).get("values", [])
        patch["test_data"] = {**base.get("test_data", {}), "changed_boundary_values": values}
        patch["expected_result_doc"] = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": f"Hệ thống chấp nhận các giá trị biên mới {', '.join(map(str, values))}"}]}]}
    return patch


def require_pending_revision(proposal, payload, allow_partial=False):
    allowed = {"PENDING", "APPLY_PARTIAL"} if allow_partial else {"PENDING"}
    if proposal["status"] not in allowed:
        raise HTTPException(status_code=409, detail={"code": "PROPOSAL_ALREADY_REVIEWED"})
    if proposal["revision"] != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT", "current_revision": proposal["revision"]})
