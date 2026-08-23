from __future__ import annotations

import re
from statistics import mean
from typing import Any

from src.services.blueprint import difficulty_level
from src.services.validation import text_projection


def document_node_counts(value: Any):
    counts: dict[str, int] = {}

    def visit(node: Any):
        if isinstance(node, dict):
            node_type = node.get("type")
            if isinstance(node_type, str):
                counts[node_type] = counts.get(node_type, 0) + 1
            for child in node.values():
                visit(child)
        elif isinstance(node, list):
            for child in node:
                visit(child)

    visit(value)
    return counts


def bounded(value: float):
    return round(max(1.0, min(5.0, value)), 3)


def predict_difficulty(
    question: dict[str, Any],
    model_version: str,
    historical_items: list[dict[str, Any]] | None = None,
):
    historical_items = historical_items or []
    stem_text = text_projection(question.get("stem_doc", {}))
    option_text = " ".join(text_projection(option.get("content_doc", {})) for option in question.get("options", []))
    solution_text = text_projection(question.get("solution_doc", {}))
    combined_text = " ".join((stem_text, option_text, solution_text))
    word_count = len(stem_text.split())
    option_count = len(question.get("options", []))
    reasoning_steps = int(question.get("construct", {}).get("reasoning_steps", 1))
    cognitive = question.get("cognitive_level") or "recognition"
    cognitive_weight = {
        "recognition": 0.0,
        "understanding": 0.35,
        "comprehension": 0.35,
        "application": 0.7,
        "analysis": 1.0,
    }.get(cognitive, 0.4)
    type_weight = {
        "true_false": 0.0,
        "single_choice": 0.1,
        "multiple_choice": 0.3,
        "matching": 0.35,
        "ordering": 0.4,
        "numeric": 0.45,
        "short_answer": 0.5,
        "symbolic_math": 0.65,
        "essay": 0.75,
    }.get(question.get("question_type"), 0.25)
    node_counts = document_node_counts(
        [question.get("stem_doc", {}), question.get("solution_doc", {}), *[option.get("content_doc", {}) for option in question.get("options", [])]]
    )
    math_node_count = sum(node_counts.get(name, 0) for name in ("mathInline", "mathBlock", "inlineMath", "blockMath"))
    image_count = node_counts.get("image", 0)
    table_count = node_counts.get("table", 0)
    numeric_token_count = len(re.findall(r"(?<!\w)-?\d+(?:[.,]\d+)?", combined_text))
    operator_count = len(re.findall(r"[+\-*/=<>^√∫∑]", combined_text))
    concept_count = len(set(question.get("concept_ids", [])))
    skill_count = len(set(question.get("skill_ids", [])))
    prerequisite_count = len(set(question.get("construct", {}).get("expected_prerequisites", [])))
    expected_exposure = question.get("construct", {}).get("expected_exposure")
    exposure_weight = {
        "new": 0.4,
        "limited": 0.25,
        "familiar": 0.0,
        "mastered": -0.2,
    }.get(expected_exposure, 0.0)
    teacher_material_evidence_count = sum(1 for item in question.get("source_evidence", []) if item.get("source_type") == "teacher_material")
    representation_complexity = min((math_node_count + image_count + table_count * 2) / 6, 0.6)
    numeric_complexity = min((numeric_token_count + operator_count) / 20, 0.5)
    construct_complexity = min((concept_count + skill_count) / 8, 0.5)
    information_density = min(word_count / max(30, option_count * 25), 0.5)
    heuristic = bounded(
        1.15
        + min(word_count / 70, 0.8)
        + min(reasoning_steps / 5, 1.0)
        + cognitive_weight
        + type_weight
        + representation_complexity
        + numeric_complexity
        + construct_complexity
        + information_density
        + min(prerequisite_count / 8, 0.4)
        + exposure_weight
    )
    historical_values = [
        float(item["difficulty"])
        for item in historical_items
        if isinstance(item.get("difficulty"), (int, float))
    ]
    historical_mean = mean(historical_values) if historical_values else None
    previous_revision_values = [
        float(item["difficulty"])
        for item in historical_items
        if item.get("same_logical_question") and isinstance(item.get("difficulty"), (int, float))
    ]
    predicted = bounded(heuristic * 0.75 + historical_mean * 0.25) if historical_mean is not None else heuristic
    evidence_count = len(question.get("source_evidence", []))
    source_types = sorted({str(item.get("source_type")) for item in question.get("source_evidence", []) if item.get("source_type")})
    confidence = round(
        min(
            0.9,
            0.38
            + 0.06 * min(evidence_count, 4)
            + (0.08 if question.get("curriculum_links") else 0)
            + 0.035 * min(len(historical_values), 5)
            + (0.04 if question.get("construct", {}).get("learning_objective") else 0),
        ),
        3,
    )
    curriculum_link = (question.get("curriculum_links") or [{}])[0]
    return {
        "method": "structured_cold_start",
        "predictor_kind": "structured",
        "predicted_difficulty": predicted,
        "heuristic_difficulty": heuristic,
        "nearest_historical_difficulty": historical_values[0] if historical_values else None,
        "historical_mean_difficulty": round(historical_mean, 3) if historical_mean is not None else None,
        "ui_difficulty_level": difficulty_level(predicted),
        "confidence": confidence,
        "uncertainty": round(1 - confidence, 3),
        "feature_snapshot": {
            "word_count": word_count,
            "option_count": option_count,
            "reasoning_steps": reasoning_steps,
            "cognitive_level": cognitive,
            "question_type": question.get("question_type"),
            "curriculum_link_count": len(question.get("curriculum_links", [])),
            "concept_count": concept_count,
            "skill_count": skill_count,
            "prerequisite_count": prerequisite_count,
            "expected_exposure": expected_exposure,
            "math_node_count": math_node_count,
            "image_count": image_count,
            "table_count": table_count,
            "numeric_token_count": numeric_token_count,
            "operator_count": operator_count,
            "source_types": source_types,
            "teacher_material_evidence_count": teacher_material_evidence_count,
            "historical_neighbor_count": len(historical_values),
            "historical_neighbor_mean": round(historical_mean, 3) if historical_mean is not None else None,
            "previous_revision_calibrated_difficulty": previous_revision_values[0] if previous_revision_values else None,
        },
        "model_version": model_version,
        "feature_schema_version": "assessment_item_features_v2",
        "training_data_window": "cold_start_with_prior_calibrated_neighbors",
        "curriculum_version": curriculum_link.get("curriculum_version") or curriculum_link.get("target_program"),
        "normalization_version": "difficulty_scale_1_5_v1",
        "reason_summary": [
            f"question_type {question.get('question_type')}",
            f"cognitive_level {cognitive}",
            f"reasoning_steps {reasoning_steps}",
            f"representation_complexity {round(representation_complexity, 3)}",
            f"numeric_complexity {round(numeric_complexity, 3)}",
            f"historical_neighbor_count {len(historical_values)}",
        ],
        "status": "provisional",
    }
