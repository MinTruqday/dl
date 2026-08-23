from decimal import Decimal, InvalidOperation
from typing import Any

from src.services.symbolic import symbolic_equivalent


def score_response(question: dict[str, Any], answer: dict[str, Any]):
    question_type = question["question_type"]
    answer_key = question.get("answer_key", {})
    points = float(question.get("scoring_rule", {}).get("points", 1))
    if question_type == "single_choice":
        correct = answer.get("option_id") == answer_key.get("option_id")
        return correct, points if correct else 0.0, "final"
    if question_type == "multiple_choice":
        actual = answer.get("option_ids", [])
        expected = answer_key.get("option_ids", [])
        correct = (
            isinstance(actual, list)
            and all(isinstance(value, str) for value in actual)
            and len(actual) == len(set(actual))
            and set(actual) == set(expected)
        )
        return correct, points if correct else 0.0, "final"
    if question_type == "true_false":
        if "value" not in answer or not isinstance(answer.get("value"), bool):
            return False, 0.0, "final"
        correct = answer["value"] is answer_key.get("value")
        return correct, points if correct else 0.0, "final"
    if question_type == "matching":
        expected = answer_key.get("pairs", {})
        actual = answer.get("pairs", {})
        if not expected or not isinstance(actual, dict):
            return None, 0.0, "pending_review"
        matches = sum(1 for key, value in expected.items() if actual.get(key) == value)
        score = points * matches / len(expected)
        return matches == len(expected), score, "final"
    if question_type == "ordering":
        expected = answer_key.get("order", [])
        actual = answer.get("order", [])
        correct = bool(expected) and isinstance(actual, list) and actual == expected
        return correct, points if correct else 0.0, "final"
    if question_type == "numeric":
        try:
            actual = Decimal(str(answer.get("value")))
            expected = Decimal(str(answer_key.get("value")))
            tolerance = Decimal(str(answer_key.get("tolerance", 0)))
            if (
                not actual.is_finite()
                or not expected.is_finite()
                or not tolerance.is_finite()
                or tolerance < 0
            ):
                return False, 0.0, "final"
            unit_matches = not answer_key.get("unit") or answer.get("unit") == answer_key.get(
                "unit"
            )
            correct = abs(actual - expected) <= tolerance and unit_matches
            return correct, points if correct else 0.0, "final"
        except (InvalidOperation, TypeError):
            return False, 0.0, "final"
    accepted_values = [
        str(value).strip() for value in answer_key.get("accepted", []) if str(value).strip()
    ]
    if question_type == "symbolic_math" and accepted_values:
        actual = str(answer.get("text", ""))
        correct = any(symbolic_equivalent(actual, expected) for expected in accepted_values)
        return correct, points if correct else 0.0, "final"
    accepted = {value.casefold() for value in accepted_values}
    if accepted:
        correct = str(answer.get("text", "")).strip().casefold() in accepted
        return correct, points if correct else 0.0, "final"
    return None, 0.0, "pending_review"
