from fastapi import HTTPException

from src.repositories.test_completion import find_project_settings, list_monitoring_overrides
from src.services.domain_policy import domain_policy
from src.services.exit_criteria import evaluate_exit_criteria


COMPLETION_POLICY = domain_policy("completion")


def default_completion_recommendation(gate, unresolved_items, residual_risks):
    readiness = COMPLETION_POLICY["readiness"]
    if gate == readiness["fail_status"] or any(
        item.get("severity") in set(COMPLETION_POLICY["blocking_severities"])
        for item in unresolved_items
        if isinstance(item, dict)
    ):
        return COMPLETION_POLICY["recommendations"]["failed"]
    if gate != readiness["pass_status"]:
        return COMPLETION_POLICY["recommendations"]["incomplete"]
    if residual_risks:
        return COMPLETION_POLICY["recommendations"]["residual_risk"]
    return COMPLETION_POLICY["recommendations"]["ready"]


async def reevaluate_completion_exit_criteria(plan, snapshot, completed_run_ids):
    evaluations = evaluate_exit_criteria(
        plan.get("quality_targets", []), snapshot.get("metrics") or {}, completed_run_ids
    )
    criterion_ids = {item["criterion_id"] for item in evaluations}
    evaluations.extend(
        dict(item)
        for item in snapshot.get("exit_criteria_evaluation", [])
        if item.get("criterion_id") not in criterion_ids
    )
    overrides = await list_monitoring_overrides(snapshot["_id"])
    latest = {item["criterion_id"]: item for item in overrides}
    for item in evaluations:
        override = latest.get(item["criterion_id"])
        if override:
            item.update({"status": override["status"], "overridden": True, "override": override})
    return evaluations


async def validate_completion_readiness(report):
    policy = COMPLETION_POLICY
    statuses = policy["statuses"]
    readiness = policy["readiness"]
    codes = policy["error_codes"]
    project = await find_project_settings(report["project_id"]) or {}
    settings = project.get("settings") or {}
    mandatory_incomplete = [
        item.get("run_id")
        for item in (report.get("scope_snapshot") or {}).get("runs", [])
        if item.get("mandatory", True) and item.get("status") != statuses["completed"]
    ]
    if mandatory_incomplete:
        raise HTTPException(
            status_code=409,
            detail={
                "code": codes["report_not_ready"],
                "reason_code": codes["mandatory_runs_incomplete"],
                "run_ids": mandatory_incomplete,
            },
        )
    blocker_threshold = int(
        settings.get(
            readiness["blocker_threshold_setting"],
            readiness["default_blocker_threshold"],
        )
        or readiness["default_blocker_threshold"]
    )
    open_blockers = int((report.get("defect_summary") or {}).get("open_blocker", 0) or 0)
    if open_blockers > blocker_threshold:
        raise HTTPException(
            status_code=409,
            detail={
                "code": codes["report_not_ready"],
                "reason_code": codes["blocker_threshold_exceeded"],
                "open_blockers": open_blockers,
                "threshold": blocker_threshold,
            },
        )
    ownerless_critical = [
        item.get("risk_id")
        for item in report.get("residual_risks", [])
        if item.get("severity") == readiness["critical_severity"]
        and not item.get("owner_id")
    ]
    if ownerless_critical:
        raise HTTPException(
            status_code=409,
            detail={"code": codes["risk_owner_required"], "risk_ids": ownerless_critical},
        )
    failed_criteria = [
        item.get("criterion_id")
        for item in report.get(
            "exit_criteria_evaluations", report.get("exit_criteria_evaluation", [])
        )
        if item.get("status") == readiness["fail_status"]
    ]
    if failed_criteria:
        raise HTTPException(
            status_code=409,
            detail={
                "code": codes["report_not_ready"],
                "reason_code": codes["exit_criteria_failed"],
                "criterion_ids": failed_criteria,
            },
        )
    reasonless_scope = [
        item.get("item_id")
        for item in report.get("unexecuted_scope", [])
        if not str(item.get("reason") or "").strip()
    ]
    if reasonless_scope:
        raise HTTPException(
            status_code=409,
            detail={
                "code": codes["report_not_ready"],
                "reason_code": codes["unexecuted_reason_required"],
                "item_ids": reasonless_scope,
            },
        )
