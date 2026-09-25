from fastapi import HTTPException

from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.repositories import regression_recommendation_repository
from src.services.domain_policy import domain_policy


REGRESSION_POLICY = domain_policy("regression_recommendation")


async def recent_failure_versions(project_id):
    policy = REGRESSION_POLICY
    runs = await regression_recommendation_repository.list_recent_runs(
        project_id, policy["recent_run_limit"]
    )
    results = await regression_recommendation_repository.list_results_by_status(
        [item["_id"] for item in runs],
        policy["failed_result_status"],
        policy["recent_result_limit"],
    )
    return {item["test_case_version_id"] for item in results}


async def create_regression_recommendation_record(change_set_id, user):
    policy = REGRESSION_POLICY
    change_set = await get_project_entity(
        policy["change_set_collection"], change_set_id, user, policy["generate_permission"]
    )
    await get_project(change_set["project_id"], user, policy["ai_generate_permission"])
    existing = await regression_recommendation_repository.find_by_change_set(change_set_id)
    if existing:
        return existing
    analysis = await regression_recommendation_repository.find_latest_impact_analysis(
        change_set_id
    )
    if not analysis:
        raise HTTPException(status_code=409, detail={"code": policy["impact_required_code"]})
    if analysis.get("status") != policy["reviewed_impact_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["impact_review_required_code"]})
    recent_failures = await recent_failure_versions(change_set["project_id"])
    items = []
    for impact in analysis.get("reviewed_affected_test_cases", analysis["affected_test_cases"]):
        test_case = await regression_recommendation_repository.find_test_case(
            impact["test_case_id"], change_set["project_id"]
        )
        current_version_id = (
            test_case.get("current_version_id") if test_case else impact["test_case_version_id"]
        )
        direct_trace = any(item.get("direct_trace") for item in impact.get("evidence", []))
        level = (
            policy["must_run_level"]
            if direct_trace
            or impact["classification"] == policy["update_classification"]
            or current_version_id in recent_failures
            else policy["should_run_level"]
            if impact["classification"] == policy["potential_classification"]
            else policy["optional_level"]
        )
        reasons = list(impact["reasons"])
        if current_version_id in recent_failures:
            reasons.append(policy["recent_failure_reason"])
        items.append(
            {
                "test_case_id": impact["test_case_id"],
                "test_case_version_id": current_version_id,
                "test_case_key": impact.get("test_case_key"),
                "level": level,
                "reasons": reasons,
                "evidence": impact["evidence"],
            }
        )
    recommendation = {
        "_id": new_id(policy["recommendation_id_prefix"]),
        "project_id": change_set["project_id"],
        "change_set_id": change_set_id,
        "impact_analysis_id": analysis["_id"],
        "items": items,
        "status": policy["pending_status"],
        "revision": policy["initial_revision"],
        "model_version": policy["model_version"],
        "created_by": user.id,
        "created_at": now(),
        "updated_at": now(),
    }
    await regression_recommendation_repository.insert_recommendation(recommendation)
    await audit(
        user.id,
        policy["created_event"],
        policy["recommendation_entity"],
        recommendation["_id"],
        change_set["project_id"],
    )
    return recommendation


async def get_change_set_regression_record(change_set_id, user):
    change_set = await get_project_entity(
        REGRESSION_POLICY["change_set_collection"],
        change_set_id,
        user,
        REGRESSION_POLICY["read_permission"],
    )
    recommendation = await regression_recommendation_repository.find_by_change_set(
        change_set_id, change_set["project_id"]
    )
    if not recommendation:
        raise HTTPException(status_code=404, detail={"code": REGRESSION_POLICY["entity_not_found_code"]})
    return recommendation


async def get_regression_recommendation_record(
    recommendation_id, user, permission=None
):
    return await get_project_entity(
        REGRESSION_POLICY["recommendation_collection"],
        recommendation_id,
        user,
        permission or REGRESSION_POLICY["read_permission"],
    )


async def edit_regression_recommendation_record(recommendation_id, payload, user):
    policy = REGRESSION_POLICY
    recommendation = await get_regression_recommendation_record(
        recommendation_id, user, policy["generate_permission"]
    )
    if recommendation.get("status") != policy["pending_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    selected = payload.selected_test_case_version_ids
    items = recommendation.get("items", [])
    if selected is not None:
        by_id = {item["test_case_version_id"]: item for item in items}
        unknown = set(selected) - set(by_id)
        if unknown:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": policy["invalid_scope_code"],
                    "test_case_version_ids": sorted(unknown),
                },
            )
        items = [by_id[item] for item in selected]
    timestamp = now()
    updated = await regression_recommendation_repository.update_recommendation(
        {
            "_id": recommendation_id,
            "project_id": recommendation["project_id"],
            "status": policy["pending_status"],
            "revision": payload.expected_revision,
        },
        {
            "items": items,
            "name": payload.name or recommendation.get("name"),
            "review_note": payload.review_note,
            "candidate_edited_by": user.id,
            "candidate_edited_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["edited_event"],
        policy["recommendation_entity"],
        recommendation_id,
        recommendation["project_id"],
    )
    return updated


async def approve_regression_recommendation_record(recommendation_id, payload, user):
    policy = REGRESSION_POLICY
    recommendation = await get_regression_recommendation_record(
        recommendation_id, user, policy["approve_permission"]
    )
    if recommendation.get("status") == policy["approved_status"] and recommendation.get(
        "test_suite_id"
    ):
        suite = await regression_recommendation_repository.find_suite(
            recommendation["test_suite_id"], recommendation["project_id"]
        )
        return {"recommendation": recommendation, "test_suite": suite}
    if recommendation.get("status") != policy["pending_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["invalid_transition_code"]})
    if recommendation["revision"] != payload.expected_revision:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["revision_conflict_code"], "current_revision": recommendation["revision"]},
        )
    recommended_ids = {item["test_case_version_id"] for item in recommendation["items"]}
    selected_ids = payload.selected_test_case_version_ids
    if selected_ids is None:
        selected_ids = [
            item["test_case_version_id"]
            for item in recommendation["items"]
            if item["level"] in policy["default_selected_levels"]
        ]
    selected_ids = list(dict.fromkeys(selected_ids))
    if not selected_ids or not set(selected_ids) <= recommended_ids:
        raise HTTPException(status_code=422, detail={"code": policy["selection_invalid_code"]})
    test_cases = await regression_recommendation_repository.list_active_test_cases(
        recommendation["project_id"],
        selected_ids,
        policy["active_test_case_status"],
        len(selected_ids),
    )
    if {item["current_version_id"] for item in test_cases} != set(selected_ids):
        raise HTTPException(status_code=409, detail={"code": policy["stale_code"]})
    timestamp = now()
    suite = {
        "_id": new_id(policy["suite_id_prefix"]),
        "project_id": recommendation["project_id"],
        "name": payload.name
        or policy["suite_name_template"].format(
            change_set_id=recommendation["change_set_id"]
        ),
        "suite_type": policy["suite_type"],
        "test_case_version_ids": selected_ids,
        "source_regression_recommendation_id": recommendation_id,
        "status": policy["approved_status"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await regression_recommendation_repository.insert_suite(suite)
    recommendation = await regression_recommendation_repository.update_recommendation(
        {
            "_id": recommendation_id,
            "project_id": recommendation["project_id"],
            "revision": payload.expected_revision,
            "status": policy["pending_status"],
        },
        {
            "status": policy["approved_status"],
            "test_suite_id": suite["_id"],
            "review_note": payload.review_note,
            "approved_by": user.id,
            "approved_at": timestamp,
            "updated_at": timestamp,
        },
    )
    if not recommendation:
        await regression_recommendation_repository.delete_suite(
            suite["_id"], suite["project_id"]
        )
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["approved_event"],
        policy["recommendation_entity"],
        recommendation_id,
        recommendation["project_id"],
        {"test_suite_id": suite["_id"], "test_count": len(selected_ids)},
    )
    await audit(
        user.id,
        policy["suite_created_event"],
        policy["suite_entity"],
        suite["_id"],
        recommendation["project_id"],
        {"source_regression_recommendation_id": recommendation_id},
    )
    return {"recommendation": recommendation, "test_suite": suite}
