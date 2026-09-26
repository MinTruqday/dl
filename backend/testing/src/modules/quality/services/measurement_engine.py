import ast
import math

from src.core.common import now
from src.repositories.measurement import measurement_repository
from src.services.domain_policy import domain_policy


SAFE_EXPRESSION_NODES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Name,
    ast.Load,
    ast.Constant,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.Mod,
    ast.Pow,
    ast.USub,
    ast.UAdd,
)


def ratio(numerator, denominator):
    if not denominator:
        return None
    return round(float(numerator) * 100 / float(denominator), 4)


def validate_formula_source(formula_type, formula, data_sources):
    policy = domain_policy("measurement_formula")
    unknown_sources = sorted(set(data_sources) - set(policy["supported_data_sources"]))
    if unknown_sources:
        return {
            "valid": False,
            "errors": [{"code": policy["source_unsupported_code"], "sources": unknown_sources}],
        }
    if formula_type != policy["custom_formula_type"]:
        return {"valid": True, "errors": []}
    try:
        tree = ast.parse(formula, mode="eval")
    except SyntaxError:
        return {"valid": False, "errors": [{"code": policy["syntax_invalid_code"]}]}
    forbidden = sorted(
        {
            type(node).__name__
            for node in ast.walk(tree)
            if not isinstance(node, SAFE_EXPRESSION_NODES)
        }
    )
    if forbidden:
        return {
            "valid": False,
            "errors": [{"code": policy["operation_unsupported_code"], "nodes": forbidden}],
        }
    nodes = list(ast.walk(tree))
    if len(nodes) > policy["maximum_nodes"]:
        return {"valid": False, "errors": [{"code": policy["too_complex_code"]}]}
    if any(
        isinstance(node, ast.Constant)
        and (isinstance(node.value, bool) or not isinstance(node.value, (int, float)))
        for node in nodes
    ):
        return {"valid": False, "errors": [{"code": policy["constant_invalid_code"]}]}
    if any(
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.Pow)
        and isinstance(node.right, ast.Constant)
        and abs(node.right.value) > policy["maximum_exponent"]
        for node in nodes
    ):
        return {"valid": False, "errors": [{"code": policy["exponent_invalid_code"]}]}
    return {
        "valid": True,
        "errors": [],
        "variables": sorted({node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}),
    }


def evaluate_safe_expression(formula, variables):
    policy = domain_policy("measurement_formula")
    tree = ast.parse(formula, mode="eval")

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError(policy["constant_invalid_code"])
            return float(node.value)
        if isinstance(node, ast.Name):
            value = variables.get(node.id)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError(policy["variable_unavailable_code"])
            return float(value)
        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        left = evaluate(node.left)
        right = evaluate(node.right)
        if isinstance(node.op, ast.Add):
            result = left + right
        elif isinstance(node.op, ast.Sub):
            result = left - right
        elif isinstance(node.op, ast.Mult):
            result = left * right
        elif isinstance(node.op, ast.Div):
            result = left / right
        elif isinstance(node.op, ast.Mod):
            result = left % right
        elif isinstance(node.op, ast.Pow):
            if (
                abs(right) > policy["maximum_exponent"]
                or abs(left) > policy["maximum_base_magnitude"]
            ):
                raise ValueError(policy["exponent_invalid_code"])
            result = left**right
        else:
            raise ValueError(policy["operation_unsupported_code"])
        if not math.isfinite(result) or abs(result) > policy["maximum_result_magnitude"]:
            raise ValueError(policy["result_invalid_code"])
        return result

    return round(evaluate(tree), 6)


async def compute_custom_metric(project_id, release_id, definition):
    policy = domain_policy("measurement_formula")
    query = {"project_id": project_id}
    if release_id:
        query["release_id"] = release_id
    snapshot = await measurement_repository.find_monitoring_snapshot(project_id, release_id)
    variables = {}
    if snapshot:
        variables.update(
            {
                key: value
                for key, value in snapshot.get("metrics", {}).items()
                if isinstance(value, (int, float)) and not isinstance(value, bool)
            }
        )
    collection_names = set(policy["aggregate_collections"])
    requested = (
        collection_names
        if policy["aggregate_source"] in definition.get("data_sources", [])
        else collection_names & set(definition.get("data_sources", []))
    )
    for collection_name in requested:
        count_query = {"project_id": project_id}
        if release_id and collection_name in policy["release_scoped_collections"]:
            count_query["release_id"] = release_id
        variables[f"{collection_name}_count"] = await measurement_repository.count_collection(
            collection_name, count_query
        )
    validation = validate_formula_source(
        definition["formula_type"], definition["formula"], definition["data_sources"]
    )
    if not validation["valid"]:
        return None, {"reason": policy["definition_invalid_code"], "errors": validation["errors"]}
    missing = sorted(set(validation.get("variables", [])) - set(variables))
    if missing:
        return None, {"reason": policy["variable_unavailable_code"], "variables": missing}
    try:
        value = evaluate_safe_expression(definition["formula"], variables)
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        return None, {"reason": str(error) or policy["evaluation_failed_code"]}
    return value, {
        "formula": definition["formula"],
        "variables": {key: variables[key] for key in validation.get("variables", [])},
        "monitoring_snapshot_id": snapshot.get("_id") if snapshot else None,
    }


async def compute_metric(project_id, release_id, key):
    policy = domain_policy("measurement_formula")
    monitoring_keys = policy["monitoring_keys"]
    source = {"key": key, "release_id": release_id}
    if key in monitoring_keys:
        query = {"project_id": project_id}
        if release_id:
            query["release_id"] = release_id
        snapshot = await measurement_repository.find_monitoring_snapshot(
            project_id, release_id
        )
        if not snapshot:
            return None, source
        metrics = snapshot.get("metrics", {})
        value = metrics.get(monitoring_keys[key])
        source.update(
            {
                "monitoring_snapshot_id": snapshot["_id"],
                "monitoring_source_fingerprint": snapshot.get("source_fingerprint"),
            }
        )
        return value, source
    if key == policy["blocked_rate_key"]:
        query = {"project_id": project_id}
        if release_id:
            query["release_id"] = release_id
        snapshot = await measurement_repository.find_monitoring_snapshot(
            project_id, release_id
        )
        if not snapshot:
            return None, source
        metrics = snapshot.get("metrics", {})
        denominator = (
            int(metrics.get("pass", 0))
            + int(metrics.get("fail", 0))
            + int(metrics.get("blocked", 0))
        )
        source.update(
            {
                "monitoring_snapshot_id": snapshot["_id"],
                "blocked": metrics.get("blocked", 0),
                "decisive": denominator,
            }
        )
        return ratio(metrics.get("blocked", 0), denominator), source
    if key == policy["stale_test_ratio_key"]:
        total = await measurement_repository.count_collection(
            policy["test_case_collection"],
            {"project_id": project_id, "status": {"$ne": policy["archived_status"]}},
        )
        stale = await measurement_repository.count_collection(
            policy["test_case_collection"],
            {"project_id": project_id, "status": policy["needs_update_status"]},
        )
        source.update({"test_case_count": total, "stale_count": stale})
        return ratio(stale, total), source
    if key == policy["automation_coverage_key"]:
        total = await measurement_repository.count_collection(
            policy["test_version_collection"],
            {"project_id": project_id, "status": {"$in": policy["approved_test_statuses"]}},
        )
        automated = await measurement_repository.count_collection(
            policy["automation_script_collection"],
            {"project_id": project_id, "status": policy["approved_status"]},
        )
        source.update({"test_case_version_count": total, "approved_script_count": automated})
        return ratio(min(automated, total), total), source
    defects = {"project_id": project_id}
    runs = {"project_id": project_id}
    if release_id:
        defects["release_id"] = release_id
        runs["release_id"] = release_id
    if key == policy["defect_reopen_rate_key"]:
        total = await measurement_repository.count_collection(policy["defect_collection"], defects)
        reopened = await measurement_repository.count_collection(
            policy["defect_collection"],
            {
                **defects,
                "$or": [
                    {"reopen_count": {"$gt": 0}},
                    {"history.action": policy["reopened_status"]},
                ],
            },
        )
        source.update({"defect_count": total, "reopened_count": reopened})
        return ratio(reopened, total), source
    if key == policy["critical_defect_aging_key"]:
        rows = await measurement_repository.list_defect_dates(
            {
                **defects,
                "severity": {"$in": policy["critical_severities"]},
                "status": {"$nin": policy["closed_defect_statuses"]},
            },
            {"created_at": 1},
            policy["query_limit"],
        )
        if not rows:
            return None, source
        timestamp = now()
        value = (
            sum(max(0, (timestamp - item["created_at"]).total_seconds()) for item in rows)
            / len(rows)
            / policy["seconds_per_day"]
        )
        source["defect_ids"] = [item["_id"] for item in rows]
        return round(value, 4), source
    if key == policy["mean_time_to_retest_key"]:
        rows = await measurement_repository.list_defect_dates(
            {**defects, "resolved_at": {"$type": "date"}, "retested_at": {"$type": "date"}},
            {"resolved_at": 1, "retested_at": 1},
            policy["query_limit"],
        )
        durations = [
            (item["retested_at"] - item["resolved_at"]).total_seconds()
            / policy["seconds_per_hour"]
            for item in rows
            if item["retested_at"] >= item["resolved_at"]
        ]
        source["sample_size"] = len(durations)
        return round(sum(durations) / len(durations), 4) if durations else None, source
    if key == policy["requirement_volatility_key"]:
        total = await measurement_repository.count_collection(
            policy["requirement_collection"], {"project_id": project_id}
        )
        changed = len(await measurement_repository.distinct_changed_requirements(project_id))
        source.update({"requirement_count": total, "changed_requirement_count": changed})
        return ratio(changed, total), source
    if key == policy["proposal_acceptance_key"]:
        query = {"project_id": project_id}
        total = await measurement_repository.count_collection(
            policy["proposal_collection"], query
        )
        accepted = await measurement_repository.count_collection(
            policy["proposal_collection"],
            {**query, "status": {"$in": policy["accepted_proposal_statuses"]}},
        )
        source.update({"proposal_count": total, "accepted_count": accepted})
        return ratio(accepted, total), source
    if key == policy["regression_effectiveness_key"]:
        rows = await measurement_repository.list_regression_results(
            project_id, policy["query_limit"]
        )
        selected = sum(len(item.get("selected_test_case_ids", [])) for item in rows)
        detected = sum(len(item.get("detected_defect_ids", [])) for item in rows)
        source.update({"selected_count": selected, "detected_defect_count": detected})
        return ratio(detected, selected), source
    if key in policy["automation_stability_keys"]:
        rows = await measurement_repository.list_automation_statuses(
            runs, policy["query_limit"]
        )
        completed = [
            item for item in rows if item.get("status") in policy["completed_automation_statuses"]
        ]
        passed = sum(
            1 for item in completed if item.get("status") == policy["passed_status"]
        )
        source.update({"execution_count": len(completed), "passed_count": passed})
        return ratio(passed, len(completed)), source
    if key in policy["defect_efficiency_keys"]:
        production = await measurement_repository.count_collection(
            policy["incident_collection"],
            {"project_id": project_id, "production": True, "linked_defect_ids.0": {"$exists": True}},
        )
        removed = await measurement_repository.count_collection(
            policy["defect_collection"],
            {**defects, "status": policy["closed_status"]},
        )
        if not production:
            return None, {**source, "reason": policy["production_data_unavailable_code"]}
        denominator = production + removed
        source.update({"escaped_count": production, "removed_count": removed})
        return (
            ratio(production, denominator)
            if key == policy["escaped_defect_rate_key"]
            else ratio(removed, denominator)
        ), source
    return None, {**source, "reason": policy["metric_source_unavailable_code"]}
