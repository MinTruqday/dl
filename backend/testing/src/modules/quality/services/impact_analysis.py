from fastapi import HTTPException

from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.repositories.impact_analysis import impact_analysis_repository
from src.services.change_analysis import classify_test_impact, semantic_candidate_score
from src.services.domain_policy import domain_policy
from src.services.impact_assistance import (
    ai_new_test_requirements,
    apply_ai_impact_suggestions,
    request_impact_classification,
)


async def create_impact_analysis_record(
    change_set_id,
    project_id,
    user,
    model_version=None,
    allow_existing=True,
    supersedes=None,
    rerun_input=None,
):
    impact_policy = domain_policy("impact_analysis")
    model_version = model_version or impact_policy["model_version"]
    change_set = await get_project_entity(
        "requirement_change_sets", change_set_id, user, impact_policy["execute_permission"]
    )
    if project_id is not None and change_set["project_id"] != project_id:
        raise HTTPException(
            status_code=422, detail={"code": impact_policy["project_mismatch_code"]}
        )
    if change_set.get("status") not in impact_policy["eligible_change_statuses"]:
        raise HTTPException(
            status_code=409,
            detail={
                "code": impact_policy["change_review_required_code"],
                "status": change_set.get("status"),
            },
        )
    await get_project(change_set["project_id"], user, impact_policy["ai_permission"])
    existing = await impact_analysis_repository.find_by_change_and_model(
        change_set_id, model_version
    )
    if existing and allow_existing:
        return existing
    criteria = await impact_analysis_repository.list_acceptance_criteria(
        [change_set["from_version_id"], change_set["to_version_id"]],
        impact_policy["criterion_limit"],
    )
    source_ids = {
        change_set["from_version_id"],
        change_set["to_version_id"],
        *[item["_id"] for item in criteria],
    }
    links = await impact_analysis_repository.list_trace_links(
        change_set["project_id"],
        list(source_ids),
        impact_policy["trace_statuses"],
        impact_policy["trace_limit"],
    )
    direct_targets = {link["target_id"] for link in links}
    current_tests = await impact_analysis_repository.list_current_tests(
        change_set["project_id"],
        impact_policy["current_test_statuses"],
        impact_policy["test_limit"],
    )
    versions = await impact_analysis_repository.list_test_versions(
        [
            item["current_version_id"]
            for item in current_tests
            if item.get("current_version_id")
        ],
        impact_policy["test_limit"],
    )
    from_version = await impact_analysis_repository.find_requirement_version(
        change_set["from_version_id"], change_set["project_id"]
    )
    to_version = await impact_analysis_repository.find_requirement_version(
        change_set["to_version_id"], change_set["project_id"]
    )
    requirement_text = " ".join(
        [
            str((from_version or {}).get("plain_text_projection", "")),
            str((to_version or {}).get("plain_text_projection", "")),
        ]
    )
    impacted = []
    for version in versions:
        direct_trace = version["_id"] in direct_targets
        semantic_score = semantic_candidate_score(
            requirement_text, str(version.get("plain_text_projection", ""))
        )
        item = classify_test_impact(version, change_set["changes"], direct_trace)
        if not direct_trace and semantic_score >= impact_policy["semantic_candidate_minimum"]:
            item["classification"] = impact_policy["potentially_affected_classification"]
            item["confidence"] = max(
                item["confidence"],
                round(
                    min(
                        impact_policy["semantic_confidence_maximum"],
                        impact_policy["semantic_confidence_base"]
                        + semantic_score * impact_policy["semantic_confidence_weight"],
                    ),
                    4,
                ),
            )
            item["reasons"].append(
                impact_policy["semantic_overlap_reason"]
            )
        item["evidence"].append(
            {
                "artifact_type": impact_policy["semantic_artifact_type"],
                "semantic_score": round(semantic_score, 4),
                "direct_trace": direct_trace,
            }
        )
        impacted.append(item)
    ai_result = await request_impact_classification(change_set["project_id"], change_set, versions)
    ai_applied_version_ids = apply_ai_impact_suggestions(impacted, ai_result)
    affected = [
        item
        for item in impacted
        if item["classification"] != impact_policy["still_valid_classification"]
        or item["test_case_version_id"] in direct_targets
    ]
    new_test_requirements = ai_new_test_requirements(ai_result, change_set["to_version_id"])
    analysis = {
        "_id": new_id(impact_policy["analysis_id_prefix"]),
        "project_id": change_set["project_id"],
        "change_set_id": change_set_id,
        "affected_test_cases": affected,
        "new_test_requirements": new_test_requirements,
        "status": impact_policy["review_ready_status"],
        "revision": impact_policy["initial_revision"],
        "mode": impact_policy["ai_mode"]
        if ai_result.get("status") == impact_policy["success_status"]
        else impact_policy["degraded_mode"],
        "model_version": model_version,
        "algorithm_version": (
            rerun_input.algorithm_version if rerun_input else impact_policy["algorithm_version"]
        ),
        "knowledge_index_version": rerun_input.knowledge_index_version if rerun_input else None,
        "snapshot_number": (
            int((supersedes or {}).get("snapshot_number", impact_policy["initial_snapshot"]))
            + 1
            if supersedes
            else impact_policy["initial_snapshot"]
        ),
        "supersedes_analysis_id": (supersedes or {}).get("_id"),
        "rerun_reason": rerun_input.reason if rerun_input else None,
        "pipeline": impact_policy["pipeline"],
        "ai_result": ai_result,
        "ai_applied_version_ids": ai_applied_version_ids,
        "created_by": user.id,
        "created_at": now(),
    }
    await impact_analysis_repository.insert_analysis(analysis)
    await impact_analysis_repository.set_change_status(
        change_set_id,
        change_set["project_id"],
        impact_policy["analyzed_status"],
        now(),
    )
    await audit(
        user.id,
        impact_policy["created_event"],
        impact_policy["entity_type"],
        analysis["_id"],
        change_set["project_id"],
        {"affected_count": len(affected)},
    )
    return analysis


async def get_change_set_impact_record(change_set_id, user):
    policy = domain_policy("impact_analysis")
    change_set = await get_project_entity(
        "requirement_change_sets", change_set_id, user, policy["read_permission"]
    )
    analysis = await impact_analysis_repository.find_latest_for_change(
        change_set_id, change_set["project_id"]
    )
    if not analysis:
        raise HTTPException(
            status_code=404, detail={"code": policy["entity_not_found_code"]}
        )
    return analysis


async def get_impact_analysis_record(analysis_id, user, permission=None):
    return await get_project_entity(
        "impact_analyses",
        analysis_id,
        user,
        permission or domain_policy("impact_analysis")["read_permission"],
    )


async def rerun_impact_analysis_record(analysis_id, payload, user):
    policy = domain_policy("impact_analysis")
    analysis = await get_impact_analysis_record(
        analysis_id, user, policy["execute_permission"]
    )
    await get_project(analysis["project_id"], user, policy["ai_permission"])
    if analysis.get("status") not in policy["rerunnable_statuses"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["not_rerunnable_code"]}
        )
    previous_status = analysis["status"]
    claimed = await impact_analysis_repository.transition_analysis(
        analysis_id,
        analysis["project_id"],
        payload.expected_revision,
        previous_status,
        {
            "status": policy["rerunning_status"],
            "rerun_requested_by": user.id,
            "rerun_requested_at": now(),
            "updated_at": now(),
        },
    )
    if not claimed:
        raise HTTPException(
            status_code=409, detail={"code": policy["revision_conflict_code"]}
        )
    snapshot_number = int(
        analysis.get("snapshot_number", policy["initial_snapshot"])
    ) + 1
    try:
        replacement = await create_impact_analysis_record(
            analysis["change_set_id"],
            analysis["project_id"],
            user,
            model_version=policy["rerun_model_template"].format(
                snapshot_number=snapshot_number
            ),
            allow_existing=False,
            supersedes=analysis,
            rerun_input=payload,
        )
        superseded = await impact_analysis_repository.transition_analysis(
            analysis_id,
            analysis["project_id"],
            claimed["revision"],
            policy["rerunning_status"],
            {
                "status": policy["superseded_status"],
                "superseded_by_analysis_id": replacement["_id"],
                "superseded_at": now(),
                "superseded_by": user.id,
                "updated_at": now(),
            },
        )
        if not superseded:
            await impact_analysis_repository.delete_analysis(
                replacement["_id"], analysis["project_id"]
            )
            raise HTTPException(
                status_code=409, detail={"code": policy["rerun_conflict_code"]}
            )
    except Exception:
        await impact_analysis_repository.restore_analysis_status(
            analysis_id,
            analysis["project_id"],
            policy["rerunning_status"],
            previous_status,
            now(),
        )
        await impact_analysis_repository.set_change_status(
            analysis["change_set_id"],
            analysis["project_id"],
            policy["reviewed_status"]
            if previous_status == policy["reviewed_status"]
            else policy["analyzed_status"],
            now(),
        )
        raise
    await audit(
        user.id,
        policy["rerun_event"],
        policy["entity_type"],
        replacement["_id"],
        analysis["project_id"],
        {
            "supersedes_analysis_id": analysis_id,
            "reason": payload.reason,
            "algorithm_version": payload.algorithm_version,
            "knowledge_index_version": payload.knowledge_index_version,
        },
    )
    return replacement


async def review_impact_analysis_record(analysis_id, payload, user):
    policy = domain_policy("impact_analysis")
    analysis = await get_impact_analysis_record(
        analysis_id, user, policy["close_permission"]
    )
    await get_project(analysis["project_id"], user, policy["review_permission"])
    if analysis["status"] == policy["reviewed_status"]:
        return analysis
    if analysis["status"] != policy["review_ready_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["invalid_transition_code"]}
        )
    if analysis["revision"] != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={
                "code": policy["revision_conflict_code"],
                "current_revision": analysis["revision"],
            },
        )
    if payload.overrides:
        await get_project(analysis["project_id"], user, policy["override_permission"])
    by_version = {
        item["test_case_version_id"]: dict(item) for item in analysis["affected_test_cases"]
    }
    unknown = [
        item.test_case_version_id
        for item in payload.overrides
        if item.test_case_version_id not in by_version
    ]
    if unknown:
        raise HTTPException(
            status_code=422,
            detail={
                "code": policy["invalid_override_target_code"],
                "test_case_version_ids": unknown,
            },
        )
    override_events = []
    for item in payload.overrides:
        target = by_version[item.test_case_version_id]
        override_events.append(
            {
                "test_case_version_id": item.test_case_version_id,
                "from_classification": target["classification"],
                "to_classification": item.classification,
                "reason": item.reason,
                "reviewed_by": user.id,
                "created_at": now(),
            }
        )
        target["classification"] = item.classification
        target["override_reason"] = item.reason
        target["overridden_by"] = user.id
    timestamp = now()
    updated = await impact_analysis_repository.review_analysis(
        analysis_id,
        analysis["project_id"],
        payload.expected_revision,
        policy["review_ready_status"],
        {
            "status": policy["reviewed_status"],
            "reviewed_affected_test_cases": list(by_version.values()),
            "review_overrides": override_events,
            "review_note": payload.review_note,
            "reviewed_by": user.id,
            "reviewed_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["revision_conflict_code"]}
        )
    await impact_analysis_repository.set_change_status(
        analysis["change_set_id"],
        analysis["project_id"],
        policy["reviewed_status"],
        timestamp,
    )
    analysis = await impact_analysis_repository.find_analysis(
        analysis_id, analysis["project_id"]
    )
    await audit(
        user.id,
        policy["reviewed_event"],
        policy["entity_type"],
        analysis_id,
        analysis["project_id"],
        {"override_count": len(override_events), "review_note": payload.review_note},
    )
    return analysis


async def add_impact_review_perspective_record(analysis_id, payload, user):
    policy = domain_policy("impact_analysis")
    analysis = await get_impact_analysis_record(
        analysis_id, user, policy["review_permission"]
    )
    note = str(payload.get("review_note") or "").strip()
    if not policy["review_note_minimum"] <= len(note) <= policy["review_note_maximum"]:
        raise HTTPException(
            status_code=422, detail={"code": policy["review_note_required_code"]}
        )
    perspective = {
        "_id": new_id(policy["perspective_id_prefix"]),
        "project_id": analysis["project_id"],
        "impact_analysis_id": analysis_id,
        "review_note": note,
        "reviewed_by": user.id,
        "created_at": now(),
    }
    await impact_analysis_repository.insert_perspective(perspective)
    await audit(
        user.id,
        policy["perspective_added_event"],
        policy["entity_type"],
        analysis_id,
        analysis["project_id"],
    )
    return perspective
