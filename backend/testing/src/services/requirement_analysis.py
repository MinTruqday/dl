from fastapi import HTTPException

from src.core.common import audit, get_project, get_project_entity, new_id, now
from src.repositories import requirement_analysis_repository
from src.services.change_analysis import semantic_changes
from src.services.linters import requirement_duplicate_score
from src.services.quality_policy import quality_policy
from src.services.domain_policy import domain_policy


REQUIREMENT_ANALYSIS_POLICY = domain_policy("requirement_analysis")


async def compare_requirement_versions(requirement_id, from_version_id, to_version_id, user):
    await get_project_entity("requirements", requirement_id, user, "requirement.diff.read")
    versions = await requirement_analysis_repository.list_versions(
        {
            "requirement_id": requirement_id,
            "_id": {"$in": [from_version_id, to_version_id]},
        },
        2,
    )
    by_id = {item["_id"]: item for item in versions}
    if set(by_id) != {from_version_id, to_version_id}:
        raise HTTPException(status_code=404, detail="Không tìm thấy đủ hai phiên bản")
    return {
        "from_version": by_id[from_version_id],
        "to_version": by_id[to_version_id],
        "changes": semantic_changes(by_id[from_version_id], by_id[to_version_id]),
        "comparison_algorithm_version": REQUIREMENT_ANALYSIS_POLICY[
            "comparison_algorithm_version"
        ],
    }


async def find_requirement_duplicates(project_id, payload, user):
    await get_project(project_id, user, "requirement.duplicate_check")
    query = {
        "project_id": project_id,
        "status": {
            "$nin": REQUIREMENT_ANALYSIS_POLICY["duplicate_excluded_statuses"]
        },
    }
    selected_ids = list(dict.fromkeys(payload.requirement_ids))
    if selected_ids:
        query["_id"] = {"$in": selected_ids}
    requirements = await requirement_analysis_repository.list_requirements(query)
    if selected_ids and {item["_id"] for item in requirements} != set(selected_ids):
        raise HTTPException(
            status_code=404,
            detail={"code": REQUIREMENT_ANALYSIS_POLICY["selection_not_found_code"]},
        )
    versions = await requirement_analysis_repository.list_versions(
        {
            "project_id": project_id,
            "_id": {"$in": [item["current_version_id"] for item in requirements]},
        },
        500,
    )
    criteria = await requirement_analysis_repository.list_acceptance_criteria(
        {
            "project_id": project_id,
            "requirement_version_id": {"$in": [item["_id"] for item in versions]},
        }
    )
    criteria_by_version = {}
    for criterion in criteria:
        criteria_by_version.setdefault(criterion["requirement_version_id"], []).append(criterion)
    version_by_id = {
        item["_id"]: {**item, "acceptance_criteria": criteria_by_version.get(item["_id"], [])}
        for item in versions
    }
    candidates = []
    ordered = sorted(requirements, key=lambda item: item["_id"])
    for index, left in enumerate(ordered):
        left_version = version_by_id.get(left["current_version_id"])
        if not left_version:
            continue
        for right in ordered[index + 1 :]:
            right_version = version_by_id.get(right["current_version_id"])
            if not right_version:
                continue
            score, reasons = requirement_duplicate_score(left_version, right_version)
            if score < payload.threshold:
                continue
            candidates.append(
                {
                    "left_requirement_id": left["_id"],
                    "left_requirement_label": left.get("requirement_key")
                    or left_version.get("title")
                    or left["_id"],
                    "left_version_id": left_version["_id"],
                    "right_requirement_id": right["_id"],
                    "right_requirement_label": right.get("requirement_key")
                    or right_version.get("title")
                    or right["_id"],
                    "right_version_id": right_version["_id"],
                    "score": score,
                    "match_type": REQUIREMENT_ANALYSIS_POLICY["exact_match_type"]
                    if score == 1
                    else REQUIREMENT_ANALYSIS_POLICY["semantic_match_type"],
                    "reasons": reasons,
                    "status": REQUIREMENT_ANALYSIS_POLICY["candidate_status"],
                }
            )
    candidates.sort(
        key=lambda item: (-item["score"], item["left_requirement_id"], item["right_requirement_id"])
    )
    candidates = candidates[: payload.limit]
    scoring = quality_policy()["duplicate_scoring"]["requirement"]
    scan = {
        "_id": new_id(REQUIREMENT_ANALYSIS_POLICY["selection_id_prefix"]),
        "project_id": project_id,
        "requirement_ids": selected_ids,
        "threshold": payload.threshold,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "algorithm": {
            "name": scoring["algorithm_name"],
            "lexical_weight": scoring["lexical_weight"],
            "term_weight": scoring["semantic_weight"],
            "business_rule_weight": scoring["rule_weight"],
        },
        "status": REQUIREMENT_ANALYSIS_POLICY["completed_status"],
        "created_by": user.id,
        "created_at": now(),
    }
    await requirement_analysis_repository.insert_duplicate_scan(scan)
    await audit(
        user.id,
        "requirement_duplicate_scan_completed",
        "RequirementDuplicateScan",
        scan["_id"],
        project_id,
        {"candidate_count": len(candidates), "threshold": payload.threshold},
    )
    return scan
