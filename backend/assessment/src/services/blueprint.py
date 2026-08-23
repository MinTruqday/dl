from typing import Any


def validate_blueprint(blueprint: dict[str, Any]):
    total = blueprint["total_questions"]
    allocated = sum(blueprint["difficulty_distribution"].values())
    issues = []
    if total != allocated:
        issues.append(
            {
                "code": "difficulty_sum_mismatch",
                "severity": "BLOCKER",
                "expected": total,
                "actual": allocated,
            }
        )
    type_total = sum(blueprint.get("question_type_constraints", {}).values())
    if type_total and type_total != total:
        issues.append(
            {
                "code": "question_type_sum_mismatch",
                "severity": "BLOCKER",
                "expected": total,
                "actual": type_total,
            }
        )
    cognitive_total = sum(blueprint.get("cognitive_level_constraints", {}).values())
    if cognitive_total and cognitive_total != total:
        issues.append(
            {
                "code": "cognitive_level_sum_mismatch",
                "severity": "BLOCKER",
                "expected": total,
                "actual": cognitive_total,
            }
        )
    for constraint in blueprint.get("coverage_constraints", []):
        if constraint.get("minimum_count", 0) > total:
            issues.append(
                {
                    "code": "coverage_constraint_impossible",
                    "severity": "BLOCKER",
                    "constraint": constraint,
                }
            )
    ability_band = blueprint.get("target_learner", {}).get("ability_band")
    if ability_band is not None and (
        not isinstance(ability_band, list)
        or len(ability_band) != 2
        or not all(isinstance(value, (int, float)) for value in ability_band)
        or not 1 <= ability_band[0] <= ability_band[1] <= 5
    ):
        issues.append({"code": "target_learner_ability_band_invalid", "severity": "BLOCKER"})
    learner_confidence = blueprint.get("target_learner", {}).get("confidence")
    if learner_confidence is not None and (
        not isinstance(learner_confidence, (int, float)) or not 0 <= learner_confidence <= 1
    ):
        issues.append({"code": "target_learner_confidence_invalid", "severity": "BLOCKER"})
    return {"valid": not issues, "issues": issues, "missing_or_excess": total - allocated}


def difficulty_level(value: float):
    return max(1, min(5, round(value)))
