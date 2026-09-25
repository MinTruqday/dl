from difflib import SequenceMatcher

from src.core.common import plain_text
from src.repositories.analysis import analysis_repository
from src.services.domain_policy import domain_policy


def confidence_band(score, policy):
    if score >= policy["high_confidence_minimum"]:
        return policy["high_confidence_band"]
    if score >= policy["medium_confidence_minimum"]:
        return policy["medium_confidence_band"]
    return policy["low_confidence_band"]


async def find_duplicate_defect_pairs(project_id):
    policy = domain_policy("duplicate_detection")
    defects = await analysis_repository.list_active_defects(
        project_id, set(policy["defect_excluded_statuses"])
    )
    pairs = []
    for index, left in enumerate(defects):
        left_text = " ".join(
            [left.get("title", ""), plain_text(left.get("description_doc", {}))]
        ).lower()
        for right in defects[index + 1 :]:
            right_text = " ".join(
                [right.get("title", ""), plain_text(right.get("description_doc", {}))]
            ).lower()
            similarity = round(SequenceMatcher(None, left_text, right_text).ratio(), 4)
            if similarity < policy["defect_minimum"]:
                continue
            pairs.append(
                {
                    "_id": f"{left['_id']}:{right['_id']}",
                    "left": left,
                    "right": right,
                    "similarity": similarity,
                    "reason": policy["defect_similarity_reason"],
                }
            )
    pairs.sort(key=lambda item: item["similarity"], reverse=True)
    return pairs[: policy["maximum_pairs"]]


async def build_defect_trace_candidates(defect):
    policy = domain_policy("defect_trace")
    text = " ".join(
        [
            defect.get("title", ""),
            plain_text(defect.get("description_doc", {})),
            plain_text(defect.get("actual_result_doc", {})),
            plain_text(defect.get("expected_result_doc", {})),
        ]
    ).lower()
    requirements = await analysis_repository.list_current_requirements(
        defect["project_id"], policy["current_requirement_excluded_status"]
    )
    requirement_version_ids = [
        item.get("current_version_id") for item in requirements if item.get("current_version_id")
    ]
    requirement_versions = await analysis_repository.list_requirement_versions(
        defect["project_id"], requirement_version_ids
    )
    requirement_by_version = {
        item.get("current_version_id"): item
        for item in requirements
        if item.get("current_version_id")
    }
    test_cases = await analysis_repository.list_current_test_cases(
        defect["project_id"],
        policy["current_test_case_excluded_status"],
        limit=2000,
    )
    current_ids = [
        item.get("current_version_id") for item in test_cases if item.get("current_version_id")
    ]
    versions = await analysis_repository.list_test_case_versions(
        defect["project_id"], current_ids, limit=2000
    )
    linked_requirements = set(defect.get("linked_requirement_version_ids", []))
    linked_test_version = next(
        (item for item in versions if item["_id"] == defect.get("linked_test_case_version_id")),
        None,
    )
    linked_test_requirements = set(
        linked_test_version.get("requirement_version_ids", []) if linked_test_version else []
    )
    requirement_candidates = []
    for version in requirement_versions:
        requirement = requirement_by_version.get(version["_id"], {})
        version_text = " ".join(
            [
                requirement.get("title", ""),
                version.get("title", ""),
                version.get("plain_text_projection", ""),
                plain_text(version.get("content_doc", {})),
            ]
        ).lower()
        similarity = SequenceMatcher(None, text, version_text).ratio()
        direct = version["_id"] in linked_requirements
        test_trace = version["_id"] in linked_test_requirements
        score = min(
            1,
            similarity * policy["text_weight"]
            + (policy["requirement_direct_increment"] if direct else 0)
            + (policy["requirement_test_trace_increment"] if test_trace else 0),
        )
        if score < policy["requirement_minimum"]:
            continue
        reasons = []
        if direct:
            reasons.append(policy["current_requirement_reason"])
        if test_trace:
            reasons.append(policy["linked_test_reason"])
        if similarity >= policy["requirement_text_reason_minimum"]:
            reasons.append(policy["similar_requirement_reason"])
        requirement_candidates.append(
            {
                "candidate_id": f"requirement_version:{version['_id']}",
                "artifact_type": policy["requirement_artifact_type"],
                "artifact_id": version["_id"],
                "requirement_id": version["requirement_id"],
                "requirement_key": version.get("requirement_key")
                or requirement.get("requirement_key"),
                "title": version.get("title") or requirement.get("title", ""),
                "confidence": round(score, 4),
                "confidence_band": confidence_band(score, policy),
                "reason_codes": reasons,
                "evidence": [
                    {
                        "artifact_type": policy["defect_artifact_type"],
                        "artifact_id": defect["_id"],
                    },
                    {
                        "artifact_type": policy["requirement_artifact_type"],
                        "artifact_id": version["_id"],
                    },
                ],
                "proposed_change": {
                    "operation": policy["add_requirement_operation"],
                    "linked_requirement_version_id": version["_id"],
                },
            }
        )
    test_case_candidates = []
    for version in versions:
        version_text = " ".join(
            [version.get("title", ""), version.get("plain_text_projection", "")]
        ).lower()
        similarity = SequenceMatcher(None, text, version_text).ratio()
        shared_requirements = linked_requirements & set(version.get("requirement_version_ids", []))
        direct = defect.get("linked_test_case_version_id") == version["_id"]
        score = min(
            1,
            similarity * policy["text_weight"]
            + (policy["test_shared_requirement_increment"] if shared_requirements else 0)
            + (policy["test_direct_increment"] if direct else 0),
        )
        if score < policy["test_minimum"]:
            continue
        reasons = []
        if direct:
            reasons.append(policy["current_test_reason"])
        if shared_requirements:
            reasons.append(policy["shared_requirement_reason"])
        if similarity >= policy["test_text_reason_minimum"]:
            reasons.append(policy["similar_behavior_reason"])
        test_case_candidates.append(
            {
                "candidate_id": f"test_case_version:{version['_id']}",
                "artifact_type": policy["test_case_artifact_type"],
                "artifact_id": version["_id"],
                "test_case_id": version["test_case_id"],
                "test_case_version_id": version["_id"],
                "test_case_key": version["test_case_key"],
                "title": version["title"],
                "requirement_version_ids": version.get("requirement_version_ids", []),
                "confidence": round(score, 4),
                "confidence_band": confidence_band(score, policy),
                "reason_codes": reasons,
                "evidence": [
                    {
                        "artifact_type": policy["defect_artifact_type"],
                        "artifact_id": defect["_id"],
                    },
                    {
                        "artifact_type": policy["test_case_artifact_type"],
                        "artifact_id": version["_id"],
                    },
                ],
                "proposed_change": {
                    "operation": policy["set_test_case_operation"],
                    "linked_test_case_version_id": version["_id"],
                },
            }
        )
    requirement_candidates.sort(key=lambda item: item["confidence"], reverse=True)
    test_case_candidates.sort(key=lambda item: item["confidence"], reverse=True)
    maximum = policy["maximum_candidates"]
    return requirement_candidates[:maximum], test_case_candidates[:maximum]
