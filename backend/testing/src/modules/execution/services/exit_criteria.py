from functools import lru_cache

from pymongo import MongoClient

from src.core.configuration import settings
from src.schemas.test_monitoring import ExitCriterionDefinition


@lru_cache(maxsize=1)
def exit_criteria_policy():
    client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        document = client[settings.TESTING_DB_NAME].runtime_policies.find_one(
            {"_id": "exit_criteria"}, {"_id": 0, "values": 1}
        )
    finally:
        client.close()
    if not isinstance(document, dict) or not isinstance(document.get("values"), dict):
        raise RuntimeError("Thiếu chính sách tiêu chí kết thúc")
    return document["values"]


def normalize_criterion(raw, index):
    rule_type = str(raw.get("type") or raw.get("key") or "").upper()
    rule_type = exit_criteria_policy()["normalized_types"].get(rule_type, rule_type)
    threshold = raw.get("threshold", raw.get("value"))
    supported = set(exit_criteria_policy()["metric_by_rule"]) | set(
        exit_criteria_policy()["supported_manual_types"]
    )
    if rule_type not in supported:
        rule_type = 'CUSTOM_MANUAL_GATE'
        threshold = False
    return ExitCriterionDefinition(
        criterion_id=str(
            raw.get("criterion_id")
            or raw.get("id")
            or f"{'EXIT-'}{index}"
        ),
        criterion=str(raw.get("criterion") or raw.get("name") or rule_type),
        type=rule_type,
        threshold=threshold,
    )


def evaluate_exit_criteria(definitions, metrics, completed_run_ids):
    policy = exit_criteria_policy()
    metric_by_rule = policy["metric_by_rule"]
    minimum_rules = set(policy["minimum_rules"])
    denominator_by_rule = policy["denominator_by_rule"]
    results = []
    for index, raw in enumerate(definitions, 1):
        definition = normalize_criterion(raw, index)
        if definition.type == 'CUSTOM_MANUAL_GATE':
            actual = None
            status = 'INSUFFICIENT_DATA'
        elif definition.type == 'REQUIRED_RUNS_COMPLETED':
            required = set(definition.threshold)
            missing = sorted(required - set(completed_run_ids))
            actual = {"completed": sorted(required & set(completed_run_ids)), "missing": missing}
            status = 'PASS' if not missing else 'FAIL'
        else:
            actual = metrics.get(metric_by_rule[definition.type], 0)
            threshold = float(definition.threshold)
            denominator_key = denominator_by_rule.get(definition.type)
            if denominator_key and not metrics.get(denominator_key, 0):
                actual = None
                status = 'INSUFFICIENT_DATA'
            else:
                if (
                    definition.type in minimum_rules
                    and 0
                    <= threshold
                    <= 1
                ):
                    threshold *= 100
                passed = (
                    actual >= threshold if definition.type in minimum_rules else actual <= threshold
                )
                status = 'PASS' if passed else 'FAIL'
        results.append(
            {
                **definition.model_dump(),
                "actual": actual,
                "status": status,
                "overridden": False,
                "evidence_refs": [],
            }
        )
    return results


def quality_gate_status(evaluations):
    if any(item["status"] == 'FAIL' for item in evaluations):
        return 'FAIL'
    incomplete = {'INSUFFICIENT_DATA', 'MANUAL_REQUIRED'}
    if any(item["status"] in incomplete for item in evaluations):
        return 'INSUFFICIENT_DATA'
    if any(item["status"] == 'WARN' for item in evaluations):
        return 'WARN'
    return 'PASS' if evaluations else 'INSUFFICIENT_DATA'
