import hashlib
import json

from fastapi import HTTPException

from src.core.database import database

PLAN_SNAPSHOT_FIELDS = (
    "project_id",
    "name",
    "objective",
    "scope_in",
    "scope_out",
    "environment",
    "environment_id",
    "entry_criteria",
    "exit_criteria",
    "risks",
    "test_types",
    "members",
    "release",
    "release_id",
    "build",
    "build_id",
    "strategy_version_id",
    "strategy_id",
    "strategy_version",
    "strategy_snapshot_hash",
    "test_level",
    "test_approach",
    "assumptions",
    "constraints",
    "dependencies",
    "stakeholders",
    "responsibility_matrix",
    "estimation",
    "schedule",
    "milestones",
    "deliverables",
    "tools",
    "suspension_criteria",
    "resumption_criteria",
    "monitoring_metrics",
    "quality_targets",
    "risk_register",
    "communication_plan",
)


def plan_snapshot(plan):
    return {field: plan.get(field) for field in PLAN_SNAPSHOT_FIELDS}


def plan_snapshot_hash(plan):
    canonical = json.dumps(
        plan_snapshot(plan), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def plan_completeness(plan, settings=None):
    settings = settings or {}
    checks = [
        (
            "TEST_PLAN_STRATEGY_REQUIRED",
            bool(plan.get("strategy_version_id") and plan.get("strategy_snapshot_hash")),
        ),
        ("TEST_PLAN_OBJECTIVE_REQUIRED", bool(str(plan.get("objective", "")).strip())),
        ("TEST_PLAN_SCOPE_REQUIRED", bool(plan.get("scope_in"))),
        ("TEST_PLAN_ENTRY_CRITERIA_REQUIRED", bool(plan.get("entry_criteria"))),
        ("TEST_PLAN_EXIT_CRITERIA_REQUIRED", bool(plan.get("exit_criteria"))),
        ("TEST_PLAN_TEST_TYPE_REQUIRED", bool(plan.get("test_types"))),
        (
            "TEST_PLAN_SCHEDULE_REQUIRED",
            bool(
                (plan.get("schedule") or {}).get("planned_start_at")
                and (plan.get("schedule") or {}).get("planned_end_at")
            ),
        ),
        ("TEST_PLAN_QUALITY_TARGET_REQUIRED", bool(plan.get("quality_targets"))),
    ]
    if settings.get("require_release_for_test_plan", True):
        checks.append(("TEST_PLAN_RELEASE_REQUIRED", bool(plan.get("release_id"))))
    if settings.get("require_environment_for_test_plan", True):
        checks.append(("TEST_PLAN_ENVIRONMENT_REQUIRED", bool(plan.get("environment_id"))))
    findings = [{"code": code, "severity": "MAJOR"} for code, passed in checks if not passed]
    return {"ready_for_approval": not findings, "findings": findings}


async def resolve_strategy_binding(project_id, strategy_version_id, auto_bind=False):
    strategy = None
    if strategy_version_id:
        strategy = await database.value.test_strategies.find_one(
            {"_id": strategy_version_id, "project_id": project_id}
        )
        if not strategy:
            raise HTTPException(status_code=422, detail={"code": "INVALID_STRATEGY_VERSION"})
        if strategy.get("status") != "APPROVED" or not strategy.get("snapshot_hash"):
            raise HTTPException(status_code=409, detail={"code": "STRATEGY_VERSION_NOT_APPROVED"})
    elif auto_bind:
        strategy = await database.value.test_strategies.find_one(
            {"project_id": project_id, "status": "APPROVED", "active_approved": True}
        )
    if not strategy:
        return {
            "strategy_version_id": None,
            "strategy_id": None,
            "strategy_version": None,
            "strategy_snapshot_hash": None,
        }
    return {
        "strategy_version_id": strategy["_id"],
        "strategy_id": strategy["lineage_id"],
        "strategy_version": strategy["version"],
        "strategy_snapshot_hash": strategy["snapshot_hash"],
    }
