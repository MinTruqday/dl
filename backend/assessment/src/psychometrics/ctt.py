import math
from collections import Counter, defaultdict
from statistics import mean, median
from typing import Any


def point_biserial(item_scores: list[float], total_scores: list[float]):
    count = len(item_scores)
    if count < 3:
        return None
    p = mean(item_scores)
    q = 1 - p
    if p <= 0 or q <= 0:
        return 0.0
    correct_totals = [total_scores[index] for index, value in enumerate(item_scores) if value > 0]
    incorrect_totals = [total_scores[index] for index, value in enumerate(item_scores) if value <= 0]
    if not correct_totals or not incorrect_totals:
        return 0.0
    overall_mean = mean(total_scores)
    variance = sum((value - overall_mean) ** 2 for value in total_scores) / count
    if variance <= 0:
        return 0.0
    return ((mean(correct_totals) - mean(incorrect_totals)) / math.sqrt(variance)) * math.sqrt(p * q)


def item_total_correlation(item_scores: list[float], total_scores: list[float]):
    if len(item_scores) < 3 or len(item_scores) != len(total_scores):
        return None
    item_mean = mean(item_scores)
    total_mean = mean(total_scores)
    numerator = sum(
        (item - item_mean) * (total - total_mean)
        for item, total in zip(item_scores, total_scores)
    )
    item_scale = math.sqrt(sum((item - item_mean) ** 2 for item in item_scores))
    total_scale = math.sqrt(sum((total - total_mean) ** 2 for total in total_scores))
    if item_scale == 0 or total_scale == 0:
        return 0.0
    return numerator / (item_scale * total_scale)


def ctt_snapshot(
    responses: list[dict[str, Any]],
    total_scores_by_attempt: dict[str, float],
    option_ids: list[str] | None = None,
    correct_option_ids: list[str] | None = None,
):
    scores = [
        (
            max(0.0, min(1.0, float(response.get("score", 0)) / float(response.get("max_score", 1))))
            if float(response.get("max_score", 1)) > 0
            else 0.0
        )
        if "score" in response
        else 1.0 if response.get("is_correct") else 0.0
        for response in responses
    ]
    rest_scores = [
        total_scores_by_attempt.get(response["attempt_id"], 0.0) - float(response.get("score", 0.0))
        for response in responses
    ]
    option_counts = Counter(str(response.get("answer", {}).get("option_id", "omitted")) for response in responses)
    omitted = sum(1 for response in responses if not response.get("answer"))
    response_times = [response.get("response_time_ms", 0) for response in responses]
    p_value = mean(scores) if scores else None
    empirical_level = 1 + 4 * (1 - p_value) if p_value is not None else None
    median_time = median(response_times) if response_times else None
    anomalous_times = sum(1 for value in response_times if median_time and (value < median_time * 0.1 or value > median_time * 10))
    correct_options = set(correct_option_ids or [])
    distractors = [option_id for option_id in option_ids or [] if option_id not in correct_options]
    functioning_distractors = [option_id for option_id in distractors if option_counts.get(option_id, 0) > 0]
    discrimination = item_total_correlation(scores, rest_scores)
    return {
        "difficulty": empirical_level,
        "p_value": p_value,
        "discrimination": discrimination,
        "item_fit_status": "insufficient_context" if discrimination is None else "productive" if discrimination >= 0.2 else "misfit" if discrimination < 0 else "review",
        "sample_size": len(responses),
        "standard_error": math.sqrt(p_value * (1 - p_value) / len(responses)) if responses and p_value is not None else None,
        "option_distribution": dict(option_counts),
        "distractor_efficiency": len(functioning_distractors) / len(distractors) if distractors else None,
        "omission_rate": omitted / len(responses) if responses else None,
        "median_response_time_ms": median_time,
        "response_time_anomaly_rate": anomalous_times / len(response_times) if response_times else None,
    }


def group_by_question(responses: list[dict[str, Any]]):
    grouped = defaultdict(list)
    for response in responses:
        grouped[response["question_version_id"]].append(response)
    return grouped
