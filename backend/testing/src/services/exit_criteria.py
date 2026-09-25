from src.domain.test_monitoring import ExitCriterionDefinition
from src.services.domain_policy import domain_policy

EXIT_POLICY = domain_policy("exit_criteria")
METRIC_BY_RULE = EXIT_POLICY["metric_by_rule"]
MINIMUM_RULES = set(EXIT_POLICY["minimum_rules"])
DENOMINATOR_BY_RULE = EXIT_POLICY["denominator_by_rule"]


def normalize_criterion(raw, index):
    policy = EXIT_POLICY
    rule_type = str(raw.get("type") or raw.get("key") or "").upper()
    rule_type = policy["aliases"].get(rule_type, rule_type)
    threshold = raw.get("threshold", raw.get("value"))
    supported = set(METRIC_BY_RULE) | {
        policy["required_runs_rule"],
        policy["manual_rule"],
    }
    if rule_type not in supported:
        rule_type = policy["manual_rule"]
        threshold = False
    return ExitCriterionDefinition(
        criterion_id=str(
            raw.get("criterion_id")
            or raw.get("id")
            or f"{policy['criterion_id_prefix']}{index}"
        ),
        criterion=str(raw.get("criterion") or raw.get("name") or rule_type),
        type=rule_type,
        threshold=threshold,
    )


def evaluate_exit_criteria(definitions, metrics, completed_run_ids):
    policy = EXIT_POLICY
    statuses = policy["statuses"]
    results = []
    for index, raw in enumerate(definitions, 1):
        definition = normalize_criterion(raw, index)
        if definition.type == policy["manual_rule"]:
            actual = None
            status = statuses["insufficient_data"]
        elif definition.type == policy["required_runs_rule"]:
            required = set(definition.threshold)
            missing = sorted(required - set(completed_run_ids))
            actual = {"completed": sorted(required & set(completed_run_ids)), "missing": missing}
            status = statuses["pass"] if not missing else statuses["fail"]
        else:
            actual = metrics.get(METRIC_BY_RULE[definition.type], 0)
            threshold = float(definition.threshold)
            denominator_key = DENOMINATOR_BY_RULE.get(definition.type)
            if denominator_key and not metrics.get(denominator_key, 0):
                actual = None
                status = statuses["insufficient_data"]
            else:
                if (
                    definition.type in MINIMUM_RULES
                    and policy["fraction_threshold_min"]
                    <= threshold
                    <= policy["fraction_threshold_max"]
                ):
                    threshold *= policy["percentage_multiplier"]
                passed = (
                    actual >= threshold if definition.type in MINIMUM_RULES else actual <= threshold
                )
                status = statuses["pass"] if passed else statuses["fail"]
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
    statuses = EXIT_POLICY["statuses"]
    if any(item["status"] == statuses["fail"] for item in evaluations):
        return statuses["fail"]
    incomplete = {statuses["insufficient_data"], statuses["manual_required"]}
    if any(item["status"] in incomplete for item in evaluations):
        return statuses["insufficient_data"]
    if any(item["status"] == statuses["warning"] for item in evaluations):
        return statuses["warning"]
    return statuses["pass"] if evaluations else statuses["insufficient_data"]
