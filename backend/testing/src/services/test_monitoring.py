from datetime import datetime, timezone

from fastapi import HTTPException

from src.core.auth import permissions_for_role
from src.core.common import audit, get_project, new_id, now, optimistic_patch
from src.core.database import database
from src.domain.test_monitoring import ControlActionCreate, ControlActionPatch, ExitCriterionOverride, MonitoringSnapshotCreate, source_fingerprint
from src.repositories.test_monitoring import find_snapshot, list_control_actions, list_snapshots
from src.services.exit_criteria import evaluate_exit_criteria, quality_gate_status


TERMINAL_RESULT_STATUSES = {"PASS", "FAIL", "BLOCKED", "SKIPPED", "NOT_APPLICABLE"}
OPEN_DEFECT_STATUSES = {"NEW", "CONFIRMED", "IN_PROGRESS", "READY_FOR_RETEST", "REOPENED"}


def percent(numerator, denominator):
    return round(numerator * 100 / denominator, 2) if denominator else 0.0


def parse_datetime(value):
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


async def monitoring_sources(project_id, plan, release_id, payload):
    run_query = {"project_id": project_id, "test_plan_id": plan["_id"]}
    if release_id:
        run_query["release_id"] = release_id
    runs = await database.value.test_runs.find(run_query).to_list(10000)
    run_ids = [item["_id"] for item in runs]
    results = await database.value.test_results.find(
        {"project_id": project_id, "test_run_id": {"$in": run_ids}}
    ).to_list(50000) if run_ids else []
    defect_query = {"project_id": project_id}
    if release_id:
        defect_query["release_id"] = release_id
    defects = await database.value.defects.find(defect_query).to_list(50000)
    requirements = await database.value.requirements.find(
        {"project_id": project_id, "status": "BASELINED"},
        {"current_version_id": 1},
    ).to_list(20000)
    requirement_version_ids = [item.get("current_version_id") for item in requirements if item.get("current_version_id")]
    criteria = await database.value.acceptance_criteria.find(
        {"project_id": project_id, "requirement_version_id": {"$in": requirement_version_ids}},
        {"_id": 1},
    ).to_list(50000) if requirement_version_ids else []
    conditions = await database.value.test_conditions.find(
        {"project_id": project_id, "status": "APPROVED"},
        {"_id": 1, "risk": 1, "revision": 1, "snapshot_hash": 1},
    ).to_list(20000)
    version_ids = sorted({version_id for run in runs for version_id in run.get("test_case_version_ids", [])})
    versions = await database.value.test_case_versions.find(
        {"project_id": project_id, "_id": {"$in": version_ids}},
        {"requirement_version_ids": 1, "acceptance_criterion_ids": 1, "test_condition_ids": 1, "source_evidence": 1, "risk": 1},
    ).to_list(50000) if version_ids else []
    api_operations = await database.value.api_operations.find(
        {"project_id": project_id}, {"_id": 1}
    ).to_list(20000)
    nfr_plans = await database.value.non_functional_test_plans.find(
        {"project_id": project_id, "status": "APPROVED"},
        {"_id": 1, "test_condition_ids": 1, "test_case_version_ids": 1, "revision": 1},
    ).to_list(5000)
    latest = await database.value.test_monitoring_snapshots.find_one(
        {"project_id": project_id, "test_plan_id": plan["_id"], "release_id": release_id},
        sort=[("snapshot_at", -1)],
    )
    since = latest.get("snapshot_at") if latest else plan.get("approved_at") or plan.get("created_at")
    changes = await database.value.requirement_change_sets.count_documents(
        {"project_id": project_id, **({"created_at": {"$gt": since}} if since else {})}
    )
    impact_pending = await database.value.impact_analyses.count_documents(
        {"project_id": project_id, "status": {"$nin": ["CLOSED", "COMPLETED"]}}
    )
    proposal_pending = await database.value.maintenance_proposals.count_documents(
        {"project_id": project_id, "status": {"$in": ["PENDING_REVIEW", "REVIEWED", "APPROVED"]}}
    )
    stale = await database.value.test_cases.count_documents(
        {"project_id": project_id, "status": "NEEDS_UPDATE"}
    )
    incident_query = {"project_id": project_id, "status": {"$in": ["OPEN", "INVESTIGATING"]}}
    if release_id:
        incident_query["$or"] = [{"build_id": {"$in": [item.get("build_id") for item in runs if item.get("build_id")]}}, {"affected_run_ids": {"$in": run_ids}}]
    incidents = await database.value.environment_incidents.find(incident_query).to_list(10000)
    return {
        "runs": runs,
        "results": results,
        "defects": defects,
        "requirements": requirements,
        "criteria": criteria,
        "conditions": conditions,
        "versions": versions,
        "api_operations": api_operations,
        "nfr_plans": nfr_plans,
        "changed_requirements": changes,
        "impact_pending": impact_pending,
        "proposal_pending": proposal_pending,
        "stale_testcases": stale,
        "environment_incidents": incidents,
        "since": since,
        "release_id": release_id,
        "actual_effort": payload.actual_effort,
        "expected_completion": payload.expected_completion,
    }


def build_metrics(plan, sources, snapshot_at):
    results = sources["results"]
    counts = {status: sum(item.get("status") == status for item in results) for status in ["NOT_RUN", "IN_PROGRESS", *TERMINAL_RESULT_STATUSES]}
    planned_test_count = len(results)
    executed_test_count = sum(counts[status] for status in TERMINAL_RESULT_STATUSES)
    decisive = counts["PASS"] + counts["FAIL"] + counts["BLOCKED"]
    versions = sources["versions"]
    covered_requirements = {item for version in versions for item in version.get("requirement_version_ids", [])}
    covered_criteria = {item for version in versions for item in version.get("acceptance_criterion_ids", [])}
    covered_conditions = {item for version in versions for item in version.get("test_condition_ids", [])}
    covered_api_operations = {
        evidence.get("artifact_id") or evidence.get("artifact_version_id")
        for version in versions
        for evidence in version.get("source_evidence", [])
        if evidence.get("artifact_type") == "api_operation"
    }
    api_operation_ids = {item["_id"] for item in sources["api_operations"]}
    executed_version_ids = {item["_id"] for item in versions}
    covered_nfr_plans = {
        item["_id"]
        for item in sources["nfr_plans"]
        if set(item.get("test_case_version_ids", [])) & executed_version_ids
        or set(item.get("test_condition_ids", [])) & covered_conditions
    }
    condition_ids = {item["_id"] for item in sources["conditions"]}
    high_risk_ids = {item["_id"] for item in sources["conditions"] if item.get("risk") in {"CRITICAL", "HIGH"}}
    defects = sources["defects"]
    open_defects = [item for item in defects if item.get("status") in OPEN_DEFECT_STATUSES]
    since = sources["since"]
    new_defects = sum(1 for item in defects if not since or bool(item.get("created_at") and item["created_at"] > since))
    resolved = sum(1 for item in defects if item.get("status") in {"RESOLVED", "READY_FOR_RETEST", "CLOSED"} and (not since or bool(item.get("updated_at") and item["updated_at"] > since)))
    reopened = sum(1 for item in defects if item.get("status") == "REOPENED" and (not since or bool(item.get("updated_at") and item["updated_at"] > since)))
    ages = [(snapshot_at - item.get("created_at")).total_seconds() / 86400 for item in open_defects if isinstance(item.get("created_at"), datetime)]
    schedule = plan.get("schedule") or {}
    planned_start = parse_datetime(schedule.get("planned_start") or schedule.get("planned_start_at"))
    planned_end = parse_datetime(schedule.get("planned_end") or schedule.get("planned_end_at"))
    actual_starts = [item.get("started_at") for item in sources["runs"] if isinstance(item.get("started_at"), datetime)]
    actual_start = min(actual_starts) if actual_starts else None
    expected_completion = sources["expected_completion"]
    schedule_variance = None
    if planned_end and expected_completion:
        schedule_variance = round((expected_completion - planned_end).total_seconds() / 86400, 2)
    planned_effort = (plan.get("estimation") or {}).get("planned_effort_hours")
    actual_effort = sources["actual_effort"]
    return {
        "planned_test_count": planned_test_count,
        "executed_test_count": executed_test_count,
        "execution_percent": percent(executed_test_count, planned_test_count),
        "pass_rate": percent(counts["PASS"], decisive),
        "not_run": counts["NOT_RUN"],
        "in_progress": counts["IN_PROGRESS"],
        "pass": counts["PASS"],
        "fail": counts["FAIL"],
        "blocked": counts["BLOCKED"],
        "skipped": counts["SKIPPED"],
        "not_applicable": counts["NOT_APPLICABLE"],
        "requirement_coverage": percent(len(covered_requirements & set(item.get("current_version_id") for item in sources["requirements"])), len(sources["requirements"])),
        "acceptance_criteria_coverage": percent(len(covered_criteria & set(item["_id"] for item in sources["criteria"])), len(sources["criteria"])),
        "test_condition_coverage": percent(len(covered_conditions & condition_ids), len(condition_ids)),
        "risk_coverage": percent(len(covered_conditions & high_risk_ids), len(high_risk_ids)),
        "api_coverage": percent(len(covered_api_operations & api_operation_ids), len(api_operation_ids)) if api_operation_ids else None,
        "nfr_coverage": percent(len(covered_nfr_plans), len(sources["nfr_plans"])) if sources["nfr_plans"] else None,
        "open_blocker": sum(item.get("severity") == "blocker" for item in open_defects),
        "open_critical": sum(item.get("severity") == "critical" for item in open_defects),
        "new_defects": new_defects,
        "resolved": resolved,
        "reopened": reopened,
        "defect_aging": round(sum(ages) / len(ages), 2) if ages else 0,
        "changed_requirements": sources["changed_requirements"],
        "stale_testcases": sources["stale_testcases"],
        "impact_pending": sources["impact_pending"],
        "proposal_pending": sources["proposal_pending"],
        "planned_start": planned_start,
        "planned_end": planned_end,
        "actual_start": actual_start,
        "expected_completion": expected_completion,
        "schedule_variance": schedule_variance,
        "planned_effort": planned_effort,
        "actual_effort": actual_effort,
        "effort_variance": round(actual_effort - planned_effort, 2) if actual_effort is not None and planned_effort is not None else None,
        "open_environment_incidents": len(sources["environment_incidents"]),
        "blocker_environment_incidents": sum(item.get("severity") in {"BLOCKER", "CRITICAL"} for item in sources["environment_incidents"]),
        "environment_downtime_seconds": sum(int(item.get("downtime") or max(0, (snapshot_at - item["observed_at"]).total_seconds())) for item in sources["environment_incidents"] if isinstance(item.get("observed_at"), datetime)),
    }


def build_deviations(metrics):
    values = []
    if metrics["schedule_variance"] is not None and metrics["schedule_variance"] > 0:
        values.append({"type": "SCHEDULE", "planned": 0, "actual": metrics["schedule_variance"], "unit": "days"})
    if metrics["effort_variance"] is not None and metrics["effort_variance"] > 0:
        values.append({"type": "EFFORT", "planned": metrics["planned_effort"], "actual": metrics["actual_effort"], "unit": "hours"})
    if metrics["blocked"]:
        values.append({"type": "BLOCKED_TESTS", "planned": 0, "actual": metrics["blocked"], "unit": "tests"})
    return values


async def create_monitoring_snapshot(project_id, payload: MonitoringSnapshotCreate, user):
    await get_project(project_id, user, "testmonitor.snapshot.create")
    plan = await database.value.test_plans.find_one({"_id": payload.test_plan_id, "project_id": project_id})
    if not plan:
        raise HTTPException(status_code=422, detail={"code": "INVALID_TEST_PLAN"})
    if plan.get("status") != "APPROVED" or not plan.get("approved_snapshot_hash"):
        raise HTTPException(status_code=409, detail={"code": "TEST_PLAN_NOT_APPROVED"})
    release_id = payload.release_id or plan.get("release_id")
    if release_id and not await database.value.releases.find_one({"_id": release_id, "project_id": project_id}, {"_id": 1}):
        raise HTTPException(status_code=422, detail={"code": "INVALID_RELEASE"})
    timestamp = now()
    sources = await monitoring_sources(project_id, plan, release_id, payload)
    metrics = build_metrics(plan, sources, timestamp)
    evaluations = evaluate_exit_criteria(plan.get("quality_targets", []), metrics, [item["_id"] for item in sources["runs"] if item.get("status") == "COMPLETED"])
    blocker_incidents = [item for item in sources["environment_incidents"] if item.get("severity") in {"BLOCKER", "CRITICAL"}]
    if blocker_incidents:
        evaluations.append({"criterion_id": "ENVIRONMENT-INCIDENT-GATE", "criterion": "Không có incident môi trường blocker hoặc critical", "type": "OPEN_ENVIRONMENT_INCIDENT_MAX", "threshold": 0, "actual": len(blocker_incidents), "status": "FAIL", "overridden": False, "evidence_refs": [item["_id"] for item in blocker_incidents]})
    source_state = {
        "plan": {"id": plan["_id"], "revision": plan["revision"], "hash": plan["approved_snapshot_hash"]},
        "runs": sorted([{"id": item["_id"], "revision": item.get("revision"), "scope_hash": item.get("frozen_scope_hash"), "status": item.get("status"), "test_case_version_ids": sorted(item.get("test_case_version_ids", [])), "release_id": item.get("release_id"), "build_id": item.get("build_id"), "environment_id": item.get("environment_id")} for item in sources["runs"]], key=lambda item: item["id"]),
        "results": sorted([{"id": item["_id"], "revision": item.get("revision"), "status": item.get("status")} for item in sources["results"]], key=lambda item: item["id"]),
        "defects": sorted([{"id": item["_id"], "revision": item.get("revision"), "status": item.get("status"), "severity": item.get("severity")} for item in sources["defects"]], key=lambda item: item["id"]),
        "conditions": sorted([{"id": item["_id"], "revision": item.get("revision"), "hash": item.get("snapshot_hash")} for item in sources["conditions"]], key=lambda item: item["id"]),
        "requirements": sorted(item.get("current_version_id") for item in sources["requirements"] if item.get("current_version_id")),
        "acceptance_criteria": sorted(item["_id"] for item in sources["criteria"]),
        "test_case_versions": sorted(
            [
                {
                    "id": item["_id"],
                    "requirements": sorted(item.get("requirement_version_ids", [])),
                    "criteria": sorted(item.get("acceptance_criterion_ids", [])),
                    "conditions": sorted(item.get("test_condition_ids", [])),
                }
                for item in sources["versions"]
            ],
            key=lambda item: item["id"],
        ),
        "api_operations": sorted(item["_id"] for item in sources["api_operations"]),
        "nfr_plans": sorted(
            ({"id": item["_id"], "revision": item.get("revision")} for item in sources["nfr_plans"]),
            key=lambda item: item["id"],
        ),
        "maintenance": {
            "changed_requirements": sources["changed_requirements"],
            "impact_pending": sources["impact_pending"],
            "proposal_pending": sources["proposal_pending"],
            "stale_testcases": sources["stale_testcases"],
        },
        "environment_incidents": sorted([{"id": item["_id"], "revision": item.get("revision"), "status": item.get("status"), "severity": item.get("severity"), "environment_id": item.get("environment_id"), "build_id": item.get("build_id")} for item in sources["environment_incidents"]], key=lambda item: item["id"]),
    }
    snapshot = {
        "_id": new_id("MONS"),
        "project_id": project_id,
        "test_plan_id": plan["_id"],
        "release_id": release_id,
        "snapshot_at": timestamp,
        "plan_revision": plan["revision"],
        "plan_snapshot_hash": plan["approved_snapshot_hash"],
        "planned": {"schedule": plan.get("schedule", {}), "estimation": plan.get("estimation", {}), "quality_targets": plan.get("quality_targets", []), "scope_in": plan.get("scope_in", []), "scope_out": plan.get("scope_out", [])},
        "actual": {"run_ids": [item["_id"] for item in sources["runs"]], "result_ids": [item["_id"] for item in sources["results"]], "defect_ids": [item["_id"] for item in sources["defects"]]},
        "metrics": metrics,
        "exit_criteria_evaluation": evaluations,
        "deviations": build_deviations(metrics),
        "risks": [*plan.get("risk_register", []), *payload.risks],
        "blockers": [*payload.blockers, *[{"defect_id": item["_id"], "severity": item.get("severity"), "title": item.get("title")} for item in sources["defects"] if item.get("status") in OPEN_DEFECT_STATUSES and item.get("severity") == "blocker"], *[{"environment_incident_id": item["_id"], "severity": item.get("severity"), "description": item.get("description")} for item in blocker_incidents]],
        "quality_gate_status": quality_gate_status(evaluations),
        "source_fingerprint": source_fingerprint(source_state),
        "source_state": source_state,
        "created_by": user.id,
        "created_at": timestamp,
        "revision": 1,
    }
    await database.value.test_monitoring_snapshots.insert_one(snapshot)
    await audit(user.id, "test_monitoring_snapshot_created", "TestMonitoringSnapshot", snapshot["_id"], project_id, {"source_fingerprint": snapshot["source_fingerprint"], "quality_gate_status": snapshot["quality_gate_status"]})
    return snapshot


async def effective_snapshot(snapshot):
    overrides = await database.value.test_monitoring_overrides.find({"snapshot_id": snapshot["_id"]}).sort("created_at", 1).to_list(1000)
    effective = [dict(item) for item in snapshot.get("exit_criteria_evaluation", [])]
    latest = {item["criterion_id"]: item for item in overrides}
    for item in effective:
        override = latest.get(item["criterion_id"])
        if override:
            item.update({"status": override["status"], "overridden": True, "override": override})
    return {**snapshot, "effective_exit_criteria_evaluation": effective, "effective_quality_gate_status": quality_gate_status(effective), "overrides": overrides}


async def get_snapshot_for_user(snapshot_id, user):
    snapshot = await find_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(snapshot["project_id"], user, "testmonitor.read")
    return await effective_snapshot(snapshot)


async def list_monitoring_snapshots(project_id, test_plan_id, release_id, limit, user):
    await get_project(project_id, user, "testmonitor.read")
    return [await effective_snapshot(item) for item in await list_snapshots(project_id, test_plan_id, release_id, limit)]


async def override_exit_criterion(snapshot_id, payload: ExitCriterionOverride, user):
    snapshot = await find_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(snapshot["project_id"], user, "testmonitor.exit_criteria.override")
    if payload.expected_revision != snapshot.get("revision", 1):
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    if payload.criterion_id not in {item["criterion_id"] for item in snapshot.get("exit_criteria_evaluation", [])}:
        raise HTTPException(status_code=404, detail={"code": "EXIT_CRITERION_NOT_FOUND"})
    value = {"_id": new_id("MONO"), "project_id": snapshot["project_id"], "snapshot_id": snapshot_id, **payload.model_dump(exclude={"expected_revision"}), "created_by": user.id, "created_at": now()}
    await database.value.test_monitoring_overrides.insert_one(value)
    await audit(user.id, "test_monitoring_exit_criterion_overridden", "TestMonitoringSnapshot", snapshot_id, snapshot["project_id"], {"criterion_id": payload.criterion_id, "status": payload.status, "reason": payload.reason, "override_id": value["_id"]})
    return await effective_snapshot(snapshot)


async def create_control_action(project_id, payload: ControlActionCreate, user):
    project = await get_project(project_id, user, "testmonitor.control.create")
    snapshot = await find_snapshot(payload.snapshot_id, project_id)
    if not snapshot:
        raise HTTPException(status_code=422, detail={"code": "INVALID_MONITORING_SNAPSHOT"})
    membership = await database.value.project_members.find_one({"project_id": project_id, "user_id": user.id, "status": "ACTIVE"})
    permissions = permissions_for_role(membership.get("project_role", ""), project.get("settings")) if membership else set()
    if payload.owner_id != user.id and "testmonitor.control.assign" not in permissions:
        raise HTTPException(status_code=403, detail={"code": "CONTROL_ACTION_ASSIGN_DENIED"})
    if not await database.value.project_members.find_one({"project_id": project_id, "user_id": payload.owner_id, "status": "ACTIVE"}, {"_id": 1}):
        raise HTTPException(status_code=422, detail={"code": "INVALID_CONTROL_ACTION_OWNER"})
    timestamp = now()
    value = {"_id": new_id("MONA"), "project_id": project_id, "plan_id": snapshot["test_plan_id"], **payload.model_dump(), "status": "OPEN", "revision": 1, "created_by": user.id, "created_at": timestamp, "updated_at": timestamp}
    await database.value.test_control_actions.insert_one(value)
    await audit(user.id, "test_control_action_created", "TestControlAction", value["_id"], project_id, {"type": value["type"], "owner_id": value["owner_id"]})
    return value


async def update_control_action(action_id, payload: ControlActionPatch, user):
    action = await database.value.test_control_actions.find_one({"_id": action_id})
    if not action:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    project = await get_project(action["project_id"], user, "testmonitor.control.update", assigned_role="TESTER", assigned_user_id=action.get("owner_id"))
    actor_membership = await database.value.project_members.find_one({"project_id": action["project_id"], "user_id": user.id, "status": "ACTIVE"})
    actor_permissions = permissions_for_role(actor_membership.get("project_role", ""), project.get("settings")) if actor_membership else set()
    if action.get("owner_id") != user.id and "testmonitor.control.assign" not in actor_permissions:
        raise HTTPException(status_code=403, detail={"code": "CONTROL_ACTION_UPDATE_DENIED"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "owner_id" in changes and changes["owner_id"] != action.get("owner_id"):
        if "testmonitor.control.assign" not in actor_permissions:
            raise HTTPException(status_code=403, detail={"code": "CONTROL_ACTION_ASSIGN_DENIED"})
        if not await database.value.project_members.find_one({"project_id": action["project_id"], "user_id": changes["owner_id"], "status": "ACTIVE"}, {"_id": 1}):
            raise HTTPException(status_code=422, detail={"code": "INVALID_CONTROL_ACTION_OWNER"})
    allowed = {"OPEN": {"IN_PROGRESS", "CANCELLED"}, "IN_PROGRESS": {"DONE", "CANCELLED"}, "DONE": set(), "CANCELLED": set()}
    if "status" in changes and changes["status"] != action["status"] and changes["status"] not in allowed[action["status"]]:
        raise HTTPException(status_code=409, detail={"code": "INVALID_STATE_TRANSITION", "from": action["status"], "to": changes["status"]})
    updated = await optimistic_patch("test_control_actions", action_id, action["project_id"], payload.expected_revision, changes)
    await audit(user.id, "test_control_action_updated", "TestControlAction", action_id, action["project_id"], {"changed_fields": sorted(changes)})
    return updated


async def list_actions_for_user(project_id, snapshot_id, status, user):
    await get_project(project_id, user, "testmonitor.read")
    return await list_control_actions(project_id, snapshot_id, status)
