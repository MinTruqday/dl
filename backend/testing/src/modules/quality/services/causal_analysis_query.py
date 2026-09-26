from fastapi import HTTPException

from src.core.common import get_project
from src.repositories.causal_analysis import causal_analysis_repository
from src.services.domain_policy import domain_policy


async def validate_member(project_id, user_id):
    policy = domain_policy("causal_analysis")
    if not await causal_analysis_repository.find_active_member(
        project_id, user_id, policy["active_member_status"]
    ):
        raise HTTPException(
            status_code=422, detail={"code": policy["action_owner_not_member_code"]}
        )


async def get_analysis(analysis_id, user, permission=None):
    policy = domain_policy("causal_analysis")
    value = await causal_analysis_repository.find_analysis(analysis_id)
    if not value:
        raise HTTPException(
            status_code=404, detail={"code": policy["error_codes"]["entity_not_found"]}
        )
    await get_project(value["project_id"], user, permission or policy["permissions"]["read"])
    return value


async def list_analyses(project_id, user):
    policy = domain_policy("causal_analysis")
    await get_project(project_id, user, "causalanalysis.read")
    items = await causal_analysis_repository.list_analyses(
        {"project_id": project_id}, policy["analysis_limit"]
    )
    return {"items": items, "total": len(items)}


async def suggest_candidates(project_id, user):
    project = await get_project(project_id, user, "causalanalysis.read")
    project_settings = project.get("settings") or {}
    policy = domain_policy("causal_analysis")
    reopen_threshold = max(
        int(
            project_settings.get(
                "rca_reopen_threshold", policy["reopen_threshold_default"]
            )
        ),
        policy["reopen_threshold_minimum"],
    )
    duplicate_threshold = max(
        int(
            project_settings.get(
                "rca_duplicate_threshold", policy["duplicate_threshold_default"]
            )
        ),
        policy["duplicate_threshold_minimum"],
    )
    defects = await causal_analysis_repository.list_defects(
        {"project_id": project_id}, policy["defect_limit"]
    )
    existing = await causal_analysis_repository.list_analyses(
        {"project_id": project_id, "status": {"$ne": policy["closed_status"]}},
        policy["analysis_limit"],
        {"defect_ids": 1},
    )
    linked = {defect_id for analysis in existing for defect_id in analysis.get("defect_ids", [])}
    duplicate_counts = {}
    root_cause_counts = {}
    for defect in defects:
        duplicate_key = defect.get("duplicate_cluster_id") or defect.get("duplicate_of")
        if duplicate_key:
            duplicate_counts[duplicate_key] = duplicate_counts.get(duplicate_key, 0) + 1
        category = defect.get("root_cause_category")
        if category and category != policy["unknown_root_cause"]:
            root_cause_counts[category] = root_cause_counts.get(category, 0) + 1
    items = []
    for defect in defects:
        if defect["_id"] in linked:
            continue
        reason_codes = []
        if str(defect.get("severity", "")).upper() in set(policy["trigger_severities"]):
            reason_codes.append(policy["reason_codes"]["severity"])
        if (
            int(defect.get("reopen_count", 0) or 0) >= reopen_threshold
            or defect.get("status") == policy["reopened_defect_status"]
        ):
            reason_codes.append(policy["reason_codes"]["reopen"])
        duplicate_key = defect.get("duplicate_cluster_id") or defect.get("duplicate_of")
        if duplicate_key and duplicate_counts.get(duplicate_key, 0) >= duplicate_threshold:
            reason_codes.append(policy["reason_codes"]["duplicate"])
        category = defect.get("root_cause_category")
        if (
            category
            and category != policy["unknown_root_cause"]
            and root_cause_counts.get(category, 0) >= duplicate_threshold
        ):
            reason_codes.append(policy["reason_codes"]["repeated_root_cause"])
        if reason_codes:
            items.append(
                {
                    "candidate_id": f"{policy['candidate_prefix']}{defect['_id']}",
                    "defect_ids": [defect["_id"]],
                    "problem_statement": defect.get("title")
                    or defect.get("summary")
                    or defect["_id"],
                    "reason_codes": reason_codes,
                    "evidence_refs": [defect["_id"]],
                }
            )
    return {
        "items": items,
        "total": len(items),
        "thresholds": {"reopen_count": reopen_threshold, "duplicate_cluster": duplicate_threshold},
    }
