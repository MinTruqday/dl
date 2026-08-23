from collections import Counter
from typing import Any


def item_matches_coverage(item: dict[str, Any], constraint: dict[str, Any]):
    values = {
        "concept": set(item.get("concept_ids", [])),
        "skill": set(item.get("skill_ids", [])),
        "curriculum_node": set(item.get("curriculum_node_ids", [])),
    }.get(constraint.get("dimension"), set())
    return bool(values.intersection(constraint.get("ids", [])))


def item_duplicate_groups(item: dict[str, Any]):
    groups = set(item.get("duplicate_groups", []))
    if item.get("duplicate_group"):
        groups.add(item["duplicate_group"])
    return groups


def selection_gaps(selected: list[dict[str, Any]], blueprint: dict[str, Any]):
    difficulty = Counter(str(item.get("difficulty_level", 3)) for item in selected)
    question_types = Counter(str(item.get("question_type", "")) for item in selected)
    cognitive = Counter(str(item.get("cognitive_level", "")) for item in selected)
    gaps = []
    if len(selected) != blueprint["total_questions"]:
        gaps.append({"code": "total_questions_unmet", "expected": blueprint["total_questions"], "actual": len(selected)})
    for level, expected in blueprint.get("difficulty_distribution", {}).items():
        if difficulty[level] != expected:
            gaps.append({"code": "difficulty_distribution_unmet", "value": level, "expected": expected, "actual": difficulty[level]})
    for question_type, expected in blueprint.get("question_type_constraints", {}).items():
        if question_types[question_type] != expected:
            gaps.append({"code": "question_type_distribution_unmet", "value": question_type, "expected": expected, "actual": question_types[question_type]})
    for level, expected in blueprint.get("cognitive_level_constraints", {}).items():
        if cognitive[level] != expected:
            gaps.append({"code": "cognitive_distribution_unmet", "value": level, "expected": expected, "actual": cognitive[level]})
    for constraint in blueprint.get("coverage_constraints", []):
        actual = sum(item_matches_coverage(item, constraint) for item in selected)
        if constraint.get("required", True) and actual < constraint.get("minimum_count", 0):
            gaps.append({"code": "coverage_constraint_unmet", "constraint": constraint, "actual": actual})
    maximum_exposure = blueprint.get("maximum_exposure_count")
    if maximum_exposure is not None:
        overexposed = [item["id"] for item in selected if int(item.get("exposure_count", 0)) > maximum_exposure]
        if overexposed:
            gaps.append({"code": "exposure_constraint_unmet", "maximum": maximum_exposure, "item_ids": overexposed})
    return gaps


def optimize_blueprint(items: list[dict[str, Any]], blueprint: dict[str, Any]):
    locked_all = sorted([item for item in items if item.get("locked")], key=lambda item: str(item["id"]))
    ineligible_locked = [item for item in locked_all if not item.get("valid", True) or item.get("status") in {"rejected", "archived"}]
    if ineligible_locked:
        return {
            "feasible": False,
            "selected": locked_all,
            "gaps": [{"code": "locked_item_ineligible", "item_ids": [item["id"] for item in ineligible_locked]}],
            "audit": [],
        }
    eligible = [item for item in items if item.get("valid", True) and item.get("status") not in {"rejected", "archived"}]
    locked = sorted([item for item in eligible if item.get("locked")], key=lambda item: str(item["id"]))
    if len(locked) > blueprint["total_questions"]:
        return {"feasible": False, "selected": locked, "gaps": [{"code": "locked_items_exceed_total"}], "audit": []}
    selected = list(locked)
    selected_ids = {item["id"] for item in selected}
    duplicate_groups = set().union(*(item_duplicate_groups(item) for item in selected)) if selected else set()
    pool = sorted(
        [
            item
            for item in eligible
            if item["id"] not in selected_ids
            and (
                blueprint.get("maximum_exposure_count") is None
                or int(item.get("exposure_count", 0)) <= blueprint["maximum_exposure_count"]
            )
        ],
        key=lambda item: (float(item.get("exposure_count", 0)), str(item["id"])),
    )
    audit = []
    while len(selected) < blueprint["total_questions"]:
        current_gaps = selection_gaps(selected, blueprint)
        difficulty_needs = Counter()
        type_needs = Counter()
        cognitive_needs = Counter()
        coverage_needs = []
        for gap in current_gaps:
            missing = max(0, int(gap.get("expected", 0)) - int(gap.get("actual", 0)))
            if gap["code"] == "difficulty_distribution_unmet":
                difficulty_needs[gap["value"]] = missing
            if gap["code"] == "question_type_distribution_unmet":
                type_needs[gap["value"]] = missing
            if gap["code"] == "cognitive_distribution_unmet":
                cognitive_needs[gap["value"]] = missing
            if gap["code"] == "coverage_constraint_unmet":
                coverage_needs.append(gap["constraint"])
        ranked = []
        selected_difficulty = Counter(str(item.get("difficulty_level", 3)) for item in selected)
        selected_types = Counter(str(item.get("question_type", "")) for item in selected)
        selected_cognitive = Counter(str(item.get("cognitive_level", "")) for item in selected)
        for item in pool:
            item_groups = item_duplicate_groups(item)
            if item_groups.intersection(duplicate_groups):
                continue
            level = str(item.get("difficulty_level", 3))
            question_type = str(item.get("question_type", ""))
            cognitive_level = str(item.get("cognitive_level", ""))
            if level in blueprint.get("difficulty_distribution", {}) and selected_difficulty[level] >= blueprint["difficulty_distribution"][level]:
                continue
            if blueprint.get("question_type_constraints") and selected_types[question_type] >= blueprint["question_type_constraints"].get(question_type, 0):
                continue
            if blueprint.get("cognitive_level_constraints") and selected_cognitive[cognitive_level] >= blueprint["cognitive_level_constraints"].get(cognitive_level, 0):
                continue
            score = 0.0
            reasons = []
            if difficulty_needs[level] > 0:
                score += 40
                reasons.append(f"difficulty_{level}")
            if type_needs[str(item.get("question_type", ""))] > 0:
                score += 30
                reasons.append("question_type")
            if cognitive_needs[str(item.get("cognitive_level", ""))] > 0:
                score += 20
                reasons.append("cognitive_level")
            coverage_matches = sum(item_matches_coverage(item, constraint) for constraint in coverage_needs)
            if coverage_matches:
                score += 100 * coverage_matches
                reasons.append("required_coverage")
            if item.get("source_kind") == "draft":
                score += 5
                reasons.append("lower_revision_cost")
            learner_fit_penalty = float(item.get("learner_fit_penalty", 0))
            construct_risk = float(item.get("construct_risk", 0))
            score -= learner_fit_penalty * 10
            score -= construct_risk * 50
            if learner_fit_penalty == 0:
                reasons.append("learner_fit")
            if construct_risk == 0:
                reasons.append("construct_safe")
            score -= float(item.get("exposure_count", 0)) * 0.01
            ranked.append((score, str(item["id"]), item, reasons))
        if not ranked:
            break
        ranked.sort(key=lambda row: (-row[0], row[1]))
        score, _, chosen, reasons = ranked[0]
        selected.append(chosen)
        selected_ids.add(chosen["id"])
        duplicate_groups.update(item_duplicate_groups(chosen))
        pool = [item for item in pool if item["id"] != chosen["id"]]
        audit.append({"item_id": chosen["id"], "score": round(score, 4), "reasons": reasons})
    gaps = selection_gaps(selected, blueprint)
    return {"feasible": not gaps, "selected": selected, "gaps": gaps, "audit": audit}
