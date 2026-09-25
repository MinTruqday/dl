from fastapi import HTTPException

from src.core.common import audit, get_project, get_project_entity, new_id, now, sort_spec
from src.core.metrics import PROPOSAL_ACCEPTANCE_RATE
from src.repositories import maintenance_proposal_repository
from src.services.domain_policy import domain_policy


async def create_maintenance_proposal_records(analysis_id, user):
    policy = domain_policy("maintenance_proposal")
    analysis = await get_project_entity("impact_analyses", analysis_id, user, "ai.create_proposal")
    if analysis.get("status") != policy["reviewed_impact_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["impact_review_required_code"]})
    existing = await maintenance_proposal_repository.list_by_impact_and_status(
        analysis_id, policy["pending_status"], policy["existing_limit"]
    )
    if existing:
        return existing
    proposals = []
    change_set = await maintenance_proposal_repository.find_change_set(
        analysis["change_set_id"]
    )
    for item in analysis.get("reviewed_affected_test_cases", analysis["affected_test_cases"]):
        if item["classification"] != policy["update_classification"]:
            continue
        patch = item.get("ai_maintenance_patch", {})
        if not patch:
            continue
        proposals.append(
            {
                "_id": new_id(policy["id_prefix"]),
                "project_id": analysis["project_id"],
                "impact_analysis_id": analysis_id,
                "proposal_type": policy["update_proposal_type"],
                "test_case_key": item.get("test_case_key"),
                "target_artifact_id": item["test_case_id"],
                "base_version_id": item["test_case_version_id"],
                "patch": patch,
                "confidence": item.get("confidence", 0),
                "reason": " · ".join(item["reasons"]),
                "evidence": item["evidence"] + change_set["changes"],
                "status": policy["pending_status"],
                "revision": 1,
                "model_version": policy["model_version"],
                "created_by": user.id,
                "created_at": now(),
                "updated_at": now(),
            }
        )
    for item in analysis.get("new_test_requirements", []):
        patch = item.get("patch", {})
        if not patch:
            continue
        proposals.append(
            {
                "_id": new_id(policy["id_prefix"]),
                "project_id": analysis["project_id"],
                "impact_analysis_id": analysis_id,
                "proposal_type": policy["create_proposal_type"],
                "target_artifact_id": None,
                "base_version_id": None,
                "patch": patch,
                "reason": item["reason"],
                "confidence": item.get("confidence", 0),
                "evidence": item["evidence"],
                "status": policy["pending_status"],
                "revision": 1,
                "model_version": policy["model_version"],
                "created_by": user.id,
                "created_at": now(),
                "updated_at": now(),
            }
        )
    if proposals:
        await maintenance_proposal_repository.insert_many(proposals)
    await audit(
        user.id,
        "maintenance_proposals_created",
        "ImpactAnalysis",
        analysis_id,
        analysis["project_id"],
        {"count": len(proposals)},
    )
    return proposals


async def list_maintenance_proposal_records(
    project_id,
    user,
    status="",
    proposal_type="",
    target_artifact_id="",
    sort="-created_at",
    limit=100,
):
    policy = domain_policy("maintenance_proposal")
    await get_project(project_id, user, "proposal.read")
    query = {"project_id": project_id}
    for field, value in {
        "status": status,
        "proposal_type": proposal_type,
        "target_artifact_id": target_artifact_id,
    }.items():
        if value:
            query[field] = value
    sort_field, direction = sort_spec(
        sort, set(policy["sort_fields"]), "-created_at"
    )
    proposals = await maintenance_proposal_repository.list_proposals(
        query, sort_field, direction, limit
    )
    base_ids = [item.get("base_version_id") for item in proposals if item.get("base_version_id")]
    bases = await maintenance_proposal_repository.list_test_case_versions(
        project_id, base_ids, limit
    )
    by_id = {item["_id"]: item for item in bases}
    analysis_ids = [
        item.get("impact_analysis_id") for item in proposals if item.get("impact_analysis_id")
    ]
    analyses = await maintenance_proposal_repository.list_impact_analyses(
        project_id, analysis_ids, limit
    )
    analyses_by_id = {item["_id"]: item for item in analyses}
    return [
        {
            **item,
            "base_version": by_id.get(item.get("base_version_id")),
            "impact_analysis": analyses_by_id.get(item.get("impact_analysis_id")),
        }
        for item in proposals
    ]


async def get_maintenance_proposal_record(proposal_id, user, permission="proposal.read"):
    return await get_project_entity("maintenance_proposals", proposal_id, user, permission)


async def review_maintenance_proposal_record(project_id, proposal_id, payload, user):
    policy = domain_policy("maintenance_proposal")
    proposal = await get_maintenance_proposal_record(proposal_id, user, "proposal.review")
    if proposal["project_id"] != project_id:
        raise HTTPException(status_code=422, detail={"code": policy["project_mismatch_code"]})
    if proposal.get("status") != policy["pending_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["not_reviewable_code"]})
    if proposal.get("revision") != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    changes = {
        "review_note": payload.review_note,
        "updated_at": now(),
        "last_reviewed_by": user.id,
        "last_reviewed_at": now(),
    }
    if payload.patch is not None:
        changes["patch"] = payload.patch
    updated = await maintenance_proposal_repository.update(
        {
            "_id": proposal_id,
            "project_id": project_id,
            "status": policy["pending_status"],
            "revision": payload.expected_revision,
        },
        changes,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id, "maintenance_proposal_reviewed", "MaintenanceProposal", proposal_id, project_id
    )
    return updated


def require_pending_revision(proposal, payload, allow_partial=False):
    policy = domain_policy("maintenance_proposal")
    allowed = (
        {policy["pending_status"], policy["partial_status"]}
        if allow_partial
        else {policy["pending_status"]}
    )
    if proposal["status"] not in allowed:
        raise HTTPException(status_code=409, detail={"code": policy["already_reviewed_code"]})
    if proposal["revision"] != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["revision_conflict_code"], "current_revision": proposal["revision"]},
        )


async def update_proposal_acceptance_rate(project_id):
    policy = domain_policy("maintenance_proposal")
    total = await maintenance_proposal_repository.count_by_statuses(
        project_id, policy["acceptance_terminal_statuses"]
    )
    accepted = await maintenance_proposal_repository.count_by_statuses(
        project_id, policy["acceptance_success_statuses"]
    )
    PROPOSAL_ACCEPTANCE_RATE.set(accepted / total if total else 0)


async def reject_maintenance_proposal_record(proposal_id, payload, user):
    policy = domain_policy("maintenance_proposal")
    proposal = await get_maintenance_proposal_record(proposal_id, user, "proposal.reject")
    if proposal.get("status") == policy["rejected_status"]:
        return proposal
    require_pending_revision(proposal, payload)
    timestamp = now()
    proposal = await maintenance_proposal_repository.update(
        {
            "_id": proposal_id,
            "project_id": proposal["project_id"],
            "status": policy["pending_status"],
            "revision": payload.expected_revision,
        },
        {
            "status": policy["rejected_status"],
            "review_note": payload.review_note,
            "reviewed_by": user.id,
            "reviewed_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not proposal:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await update_proposal_acceptance_rate(proposal["project_id"])
    await audit(
        user.id,
        "maintenance_proposal_rejected",
        "MaintenanceProposal",
        proposal_id,
        proposal["project_id"],
    )
    return proposal


async def regenerate_maintenance_proposal_record(proposal_id, payload, user):
    policy = domain_policy("maintenance_proposal")
    proposal = await get_maintenance_proposal_record(proposal_id, user, "ai.create_proposal")
    if proposal.get("status") != policy["pending_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    if proposal.get("revision") != payload.expected_revision:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    replacement = {
        **{
            key: value
            for key, value in proposal.items()
            if key
            not in {
                "_id",
                "status",
                "revision",
                "created_at",
                "updated_at",
                "reviewed_at",
                "reviewed_by",
            }
        },
        "_id": new_id(policy["id_prefix"]),
        "parent_proposal_id": proposal_id,
        "regeneration_instruction": payload.instruction,
        "status": policy["pending_status"],
        "revision": 1,
        "model_version": policy["model_version"],
        "created_by": user.id,
        "created_at": now(),
        "updated_at": now(),
    }
    updated = await maintenance_proposal_repository.update(
        {
            "_id": proposal_id,
            "project_id": proposal["project_id"],
            "status": policy["pending_status"],
            "revision": payload.expected_revision,
        },
        {
            "status": policy["superseded_status"],
            "superseded_by": replacement["_id"],
            "regeneration_instruction": payload.instruction,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    try:
        await maintenance_proposal_repository.insert(replacement)
    except Exception:
        await maintenance_proposal_repository.rollback_supersede(
            proposal_id,
            proposal["project_id"],
            replacement["_id"],
            policy["pending_status"],
            now(),
        )
        raise
    await audit(
        user.id,
        "maintenance_proposal_regenerated",
        "MaintenanceProposal",
        replacement["_id"],
        proposal["project_id"],
        {"parent_proposal_id": proposal_id},
    )
    return replacement
