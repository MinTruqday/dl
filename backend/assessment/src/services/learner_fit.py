from __future__ import annotations

import math
from collections import defaultdict
from statistics import mean
from typing import Any


def _bounded(value: float, minimum: float = 0.0, maximum: float = 1.0):
    return max(minimum, min(maximum, value))


def _success_probability(ability: float, difficulty: float):
    return 1 / (1 + math.exp(-1.35 * (ability - difficulty)))


def _category(probability: float, target_range: list[float]):
    lower, upper = target_range
    if probability > upper:
        return "too_easy"
    if probability >= lower:
        return "suitable"
    if probability >= max(0.05, lower - 0.2):
        return "challenging"
    return "too_hard"


def _fit_score(probability: float, target_range: list[float]):
    lower, upper = target_range
    if lower <= probability <= upper:
        midpoint = (lower + upper) / 2
        half_width = max((upper - lower) / 2, 0.01)
        return _bounded(1 - abs(probability - midpoint) / half_width * 0.15)
    distance = lower - probability if probability < lower else probability - upper
    return _bounded(1 - distance / max(lower, 1 - upper, 0.01))


def _topic(question: dict[str, Any]):
    links = question.get("curriculum_links") or []
    first = links[0] if links and isinstance(links[0], dict) else {}
    for key in ("concept_id", "lesson_id", "chapter_id", "section_id", "subject"):
        if first.get(key):
            return str(first[key])
    concepts = question.get("concept_ids") or []
    return str(concepts[0]) if concepts else "unmapped"


def evaluate_learner_fit(
    items: list[dict[str, Any]],
    target_learner: dict[str, Any],
    target_success_range: list[float] | None = None,
):
    target_range = target_success_range or [0.45, 0.8]
    ability_band = target_learner.get("ability_band") or [2.0, 4.0]
    lower_ability = float(ability_band[0])
    upper_ability = float(ability_band[1])
    midpoint_ability = (lower_ability + upper_ability) / 2
    learner_confidence = _bounded(float(target_learner.get("confidence", 0.4)))
    topic_ability = target_learner.get("topic_ability") or {}
    topic_confidence = target_learner.get("topic_confidence") or {}
    rows = []
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        difficulty = float(item["difficulty"])
        topic = str(item.get("topic") or _topic(item))
        topic_estimate = topic_ability.get(topic)
        ability = (
            float(topic_estimate) if isinstance(topic_estimate, (int, float)) else midpoint_ability
        )
        item_confidence = _bounded(float(item.get("confidence", 0.25)))
        local_learner_confidence = _bounded(float(topic_confidence.get(topic, learner_confidence)))
        confidence = round(min(item_confidence, local_learner_confidence), 3)
        probability = _success_probability(ability, difficulty)
        probability_low = _success_probability(lower_ability, difficulty)
        probability_high = _success_probability(upper_ability, difficulty)
        category = _category(probability, target_range)
        reasons = []
        if category == "too_easy":
            reasons.append("expected_success_above_target")
        elif category == "challenging":
            reasons.append("expected_success_below_target")
        elif category == "too_hard":
            reasons.append("difficulty_exceeds_learner_band")
        else:
            reasons.append("expected_success_within_target")
        if confidence < 0.5:
            reasons.append("low_evidence")
        if topic_estimate is None:
            reasons.append("generic_ability_band_fallback")
        row = {
            "question_id": item.get("question_id"),
            "question_draft_id": item.get("question_draft_id"),
            "question_version_id": item.get("question_version_id"),
            "topic": topic,
            "difficulty": round(difficulty, 3),
            "difficulty_source": item.get("difficulty_source", "unknown"),
            "expected_probability_correct": round(probability, 3),
            "expected_success_range": [
                round(min(probability_low, probability_high), 3),
                round(max(probability_low, probability_high), 3),
            ],
            "fit_score": round(_fit_score(probability, target_range), 3),
            "fit_category": category,
            "confidence": confidence,
            "reasons": reasons,
        }
        rows.append(row)
        grouped[topic].append(row)
    categories = {category: 0 for category in ("too_easy", "suitable", "challenging", "too_hard")}
    for row in rows:
        categories[row["fit_category"]] += 1
    per_topic = []
    for topic, topic_rows in sorted(grouped.items()):
        topic_categories = {category: 0 for category in categories}
        for row in topic_rows:
            topic_categories[row["fit_category"]] += 1
        per_topic.append(
            {
                "topic": topic,
                "item_count": len(topic_rows),
                "expected_probability_correct": round(
                    mean(row["expected_probability_correct"] for row in topic_rows), 3
                ),
                "fit_score": round(mean(row["fit_score"] for row in topic_rows), 3),
                "confidence": round(mean(row["confidence"] for row in topic_rows), 3),
                "categories": topic_categories,
            }
        )
    low_evidence_ids = [
        row.get("question_draft_id") or row.get("question_version_id")
        for row in rows
        if row["confidence"] < 0.5
    ]
    mismatch_rows = [row for row in rows if row["fit_category"] != "suitable"]
    question_count = len(rows)
    expected_score = mean(row["expected_probability_correct"] for row in rows) if rows else 0
    expected_low = mean(row["expected_success_range"][0] for row in rows) if rows else 0
    expected_high = mean(row["expected_success_range"][1] for row in rows) if rows else 0
    suitable_ratio = categories["suitable"] / question_count if question_count else 0
    return {
        "target_learner": {
            **target_learner,
            "ability_band": [lower_ability, upper_ability],
            "confidence": round(learner_confidence, 3),
            "source": target_learner.get("source", "generic_learner_band"),
        },
        "target_success_range": target_range,
        "question_count": question_count,
        "expected_fit_overall": round(mean(row["fit_score"] for row in rows), 3) if rows else 0,
        "expected_probability_correct": round(expected_score, 3),
        "expected_success_range": [round(expected_low, 3), round(expected_high, 3)],
        "confidence": round(mean(row["confidence"] for row in rows), 3) if rows else 0,
        "categories": categories,
        "per_topic": per_topic,
        "item_level_mismatch": mismatch_rows,
        "distribution_mismatch": {
            "mismatch_count": len(mismatch_rows),
            "mismatch_ratio": round(1 - suitable_ratio, 3) if question_count else 0,
            "floor_risk": round(categories["too_easy"] / question_count, 3)
            if question_count
            else 0,
            "ceiling_risk": round(categories["too_hard"] / question_count, 3)
            if question_count
            else 0,
            "over_concentration": max(categories.values()) / question_count > 0.7
            if question_count
            else False,
        },
        "low_evidence_warning": bool(low_evidence_ids),
        "low_evidence_item_ids": low_evidence_ids,
        "reason_summary": {
            "suitable_item_ratio": round(suitable_ratio, 3),
            "cold_start": learner_confidence < 0.5,
            "difficulty_sources": sorted(
                {str(item.get("difficulty_source", "unknown")) for item in items}
            ),
        },
        "items": rows,
    }
