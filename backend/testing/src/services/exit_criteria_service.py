from src.domain.test_monitoring import ExitCriterionDefinition


METRIC_BY_RULE = {
    "EXECUTION_PERCENT_MIN": "execution_percent",
    "PASS_RATE_MIN": "pass_rate",
    "OPEN_BLOCKER_MAX": "open_blocker",
    "OPEN_CRITICAL_MAX": "open_critical",
    "REQUIREMENT_COVERAGE_MIN": "requirement_coverage",
    "CONDITION_COVERAGE_MIN": "test_condition_coverage",
    "STALE_TESTCASE_MAX": "stale_testcases",
}


MINIMUM_RULES = {
    "EXECUTION_PERCENT_MIN",
    "PASS_RATE_MIN",
    "REQUIREMENT_COVERAGE_MIN",
    "CONDITION_COVERAGE_MIN",
}


def normalize_criterion(raw, index):
    rule_type = str(raw.get("type") or raw.get("key") or "").upper()
    aliases = {
        "EXECUTION_PROGRESS": "EXECUTION_PERCENT_MIN",
        "EXECUTION_PERCENT": "EXECUTION_PERCENT_MIN",
        "PASS_RATE": "PASS_RATE_MIN",
        "OPEN_BLOCKER": "OPEN_BLOCKER_MAX",
        "OPEN_CRITICAL": "OPEN_CRITICAL_MAX",
        "REQUIREMENT_COVERAGE": "REQUIREMENT_COVERAGE_MIN",
        "CONDITION_COVERAGE": "CONDITION_COVERAGE_MIN",
        "STALE_TESTCASES": "STALE_TESTCASE_MAX",
    }
    rule_type = aliases.get(rule_type, rule_type)
    threshold = raw.get("threshold", raw.get("value"))
    supported = set(METRIC_BY_RULE) | {"REQUIRED_RUNS_COMPLETED", "CUSTOM_MANUAL_GATE"}
    if rule_type not in supported:
        rule_type = "CUSTOM_MANUAL_GATE"
        threshold = False
    return ExitCriterionDefinition(
        criterion_id=str(raw.get("criterion_id") or raw.get("id") or f"EXIT-{index}"),
        criterion=str(raw.get("criterion") or raw.get("name") or rule_type),
        type=rule_type,
        threshold=threshold,
    )


def evaluate_exit_criteria(definitions, metrics, completed_run_ids):
    results = []
    for index, raw in enumerate(definitions, 1):
        definition = normalize_criterion(raw, index)
        if definition.type == "CUSTOM_MANUAL_GATE":
            actual = None
            status = "MANUAL_REQUIRED"
        elif definition.type == "REQUIRED_RUNS_COMPLETED":
            required = set(definition.threshold)
            missing = sorted(required - set(completed_run_ids))
            actual = {"completed": sorted(required & set(completed_run_ids)), "missing": missing}
            status = "PASS" if not missing else "FAIL"
        else:
            actual = metrics.get(METRIC_BY_RULE[definition.type], 0)
            threshold = float(definition.threshold)
            if definition.type in MINIMUM_RULES and 0 <= threshold <= 1:
                threshold *= 100
            passed = actual >= threshold if definition.type in MINIMUM_RULES else actual <= threshold
            status = "PASS" if passed else "FAIL"
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
    if any(item["status"] == "FAIL" for item in evaluations):
        return "FAIL"
    if any(item["status"] == "MANUAL_REQUIRED" for item in evaluations):
        return "MANUAL_REQUIRED"
    return "PASS" if evaluations else "NOT_CONFIGURED"
