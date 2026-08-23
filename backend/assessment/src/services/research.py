from math import sqrt
from statistics import mean
from typing import Any


FORBIDDEN_OUTCOME_FEATURES = {
    "calibrated_difficulty",
    "empirical_difficulty",
    "irt_b",
    "outcome",
    "p_value",
    "response_correctness",
}


def correlation(left: list[float], right: list[float]):
    if len(left) < 2 or len(left) != len(right):
        return None
    left_mean = mean(left)
    right_mean = mean(right)
    numerator = sum((x - left_mean) * (y - right_mean) for x, y in zip(left, right))
    left_scale = sqrt(sum((x - left_mean) ** 2 for x in left))
    right_scale = sqrt(sum((y - right_mean) ** 2 for y in right))
    if left_scale == 0 or right_scale == 0:
        return None
    value = numerator / (left_scale * right_scale)
    if abs(1 - value) < 1e-12:
        return 1.0
    if abs(-1 - value) < 1e-12:
        return -1.0
    return value


def ranks(values: list[float]):
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    result = [0.0] * len(values)
    position = 0
    while position < len(ordered):
        end = position + 1
        while end < len(ordered) and ordered[end][1] == ordered[position][1]:
            end += 1
        average_rank = (position + 1 + end) / 2
        for index in range(position, end):
            result[ordered[index][0]] = average_rank
        position = end
    return result


def rank_consistency(estimates: list[float], empirical: list[float]):
    compared = 0
    consistent = 0.0
    for left in range(len(estimates)):
        for right in range(left + 1, len(estimates)):
            estimate_order = estimates[left] - estimates[right]
            empirical_order = empirical[left] - empirical[right]
            if estimate_order == 0 and empirical_order == 0:
                consistent += 1
            elif estimate_order == 0 or empirical_order == 0:
                consistent += 0.5
            elif estimate_order * empirical_order > 0:
                consistent += 1
            compared += 1
    return consistent / compared if compared else None


def uncertainty_calibration(rows: list[dict[str, Any]], estimate_key: str):
    usable = [
        row
        for row in rows
        if isinstance(row.get(estimate_key), (int, float))
        and isinstance(row.get("empirical"), (int, float))
        and isinstance(row.get(f"{estimate_key}_confidence"), (int, float))
    ]
    bins = []
    weighted_gap = 0.0
    covered = 0
    total_width = 0.0
    for lower in (0.0, 0.2, 0.4, 0.6, 0.8):
        upper = lower + 0.2
        members = [
            row
            for row in usable
            if lower <= float(row[f"{estimate_key}_confidence"]) <= upper
            and (upper == 1.0 or float(row[f"{estimate_key}_confidence"]) < upper)
        ]
        if not members:
            continue
        average_confidence = mean(float(row[f"{estimate_key}_confidence"]) for row in members)
        observed_accuracy = mean(
            max(0.0, 1 - abs(float(row[estimate_key]) - float(row["empirical"])) / 4)
            for row in members
        )
        gap = abs(average_confidence - observed_accuracy)
        weighted_gap += gap * len(members)
        bins.append(
            {
                "lower": lower,
                "upper": upper,
                "count": len(members),
                "mean_confidence": average_confidence,
                "observed_accuracy": observed_accuracy,
                "absolute_gap": gap,
            }
        )
    for row in usable:
        estimate = float(row[estimate_key])
        empirical = float(row["empirical"])
        half_width = 4 * (1 - float(row[f"{estimate_key}_confidence"]))
        lower = max(1.0, estimate - half_width)
        upper = min(5.0, estimate + half_width)
        covered += int(lower <= empirical <= upper)
        total_width += upper - lower
    return {
        "count": len(usable),
        "expected_calibration_error": weighted_gap / len(usable) if usable else None,
        "prediction_interval_coverage": covered / len(usable) if usable else None,
        "mean_prediction_interval_width": total_width / len(usable) if usable else None,
        "bins": bins,
    }


def evaluation_metrics(rows: list[dict[str, Any]], estimate_key: str):
    paired = [
        row
        for row in rows
        if isinstance(row.get(estimate_key), (int, float))
        and isinstance(row.get("empirical"), (int, float))
    ]
    estimates = [float(row[estimate_key]) for row in paired]
    empirical = [float(row["empirical"]) for row in paired]
    errors = [estimate - target for estimate, target in zip(estimates, empirical)]
    absolute_errors = [abs(error) for error in errors]
    confidence_rows = [
        row for row in paired if isinstance(row.get(f"{estimate_key}_confidence"), (int, float))
    ]
    confidence = [float(row[f"{estimate_key}_confidence"]) for row in confidence_rows]
    confidence_errors = [
        abs(float(row[estimate_key]) - float(row["empirical"])) for row in confidence_rows
    ]
    return {
        "count": len(paired),
        "mae": mean(absolute_errors) if absolute_errors else None,
        "rmse": sqrt(mean([error**2 for error in errors])) if errors else None,
        "pearson": correlation(estimates, empirical),
        "spearman": correlation(ranks(estimates), ranks(empirical))
        if len(estimates) >= 2
        else None,
        "rank_consistency": rank_consistency(estimates, empirical),
        "mean_signed_error": mean(errors) if errors else None,
        "mean_confidence": mean(confidence) if confidence else None,
        "confidence_error_correlation": correlation(confidence, confidence_errors),
        "uncertainty_calibration": uncertainty_calibration(paired, estimate_key),
    }


def leakage_checks(rows: list[dict[str, Any]]):
    issues = []
    for row in rows:
        features = row.get("feature_snapshot") or {}
        forbidden = sorted(FORBIDDEN_OUTCOME_FEATURES.intersection(features))
        if forbidden:
            issues.append(
                {
                    "code": "future_outcome_feature_present",
                    "question_version_id": row.get("question_version_id"),
                    "feature_names": forbidden,
                }
            )
        prediction_time = row.get("prediction_created_at")
        calibration_time = row.get("calibration_created_at")
        if prediction_time and calibration_time and prediction_time >= calibration_time:
            issues.append(
                {
                    "code": "prediction_not_cold_start",
                    "question_version_id": row.get("question_version_id"),
                }
            )
        if row.get("is_first_exposure_only") is False:
            issues.append(
                {
                    "code": "exposure_contamination",
                    "question_version_id": row.get("question_version_id"),
                }
            )
    return {
        "passed": not issues,
        "split_unit": "logical_question_id",
        "forbidden_feature_names": sorted(FORBIDDEN_OUTCOME_FEATURES),
        "issues": issues,
    }


def calibration_stability(snapshots: list[dict[str, Any]]):
    ordered = sorted(snapshots, key=lambda row: row.get("created_at") or "")
    calibrated = [
        row
        for row in ordered
        if row.get("status") == "calibrated" and isinstance(row.get("difficulty"), (int, float))
    ]
    changes = [
        abs(float(current["difficulty"]) - float(previous["difficulty"]))
        for previous, current in zip(calibrated, calibrated[1:])
    ]
    sample_sensitivity = [
        change
        / max(1, abs(int(current.get("sample_size", 0)) - int(previous.get("sample_size", 0))))
        for previous, current, change in zip(calibrated, calibrated[1:], changes)
    ]
    latest = calibrated[-1] if calibrated else None
    difficulties = [float(row["difficulty"]) for row in calibrated]
    return {
        "snapshot_count": len(ordered),
        "calibrated_snapshot_count": len(calibrated),
        "sample_sizes": [int(row.get("sample_size", 0)) for row in ordered],
        "estimate_range": max(difficulties) - min(difficulties) if difficulties else None,
        "mean_absolute_snapshot_change": mean(changes) if changes else None,
        "mean_change_per_added_response": mean(sample_sensitivity) if sample_sensitivity else None,
        "latest_standard_error": latest.get("standard_error") if latest else None,
        "latest_sample_size": latest.get("sample_size", 0) if latest else 0,
        "latest_status": ordered[-1].get("status") if ordered else None,
        "latest_contamination_filter_difficulty_delta": latest.get(
            "contamination_filter_difficulty_delta"
        )
        if latest
        else None,
        "sample_size_monotonic": all(
            int(current.get("sample_size", 0)) >= int(previous.get("sample_size", 0))
            for previous, current in zip(ordered, ordered[1:])
        ),
    }
