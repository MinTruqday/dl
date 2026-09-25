from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.auth import permissions_for_role
from src.core.common import audit, get_project, new_id, now
from src.domain.test_monitoring import (
    ControlActionCreate,
    ControlActionPatch,
    ExitCriterionOverride,
    MonitoringSnapshotCreate,
    source_fingerprint,
)
from src.repositories.test_monitoring import test_monitoring_repository
from src.services.domain_policy import domain_policy
from src.services.exit_criteria import evaluate_exit_criteria, quality_gate_status
from src.services.quality_gate import (
    create_quality_decision,
    export_quality_gate,
    get_quality_gate,
    list_quality_decisions,
)
from src.services.test_monitoring_snapshot import (
    OPEN_DEFECT_STATUSES,
    build_deviations,
    build_metrics,
    monitoring_sources,
)

MONITORING_POLICY = domain_policy("test_monitoring")

__all__ = [
    "create_quality_decision",
    "export_quality_gate",
    "get_quality_gate",
    "list_quality_decisions",
]


async def create_monitoring_snapshot(project_id, payload: MonitoringSnapshotCreate, user):
    await get_project(project_id, user, MONITORING_POLICY["snapshot_create_permission"])
    plan = await test_monitoring_repository.find_test_plan(payload.test_plan_id, project_id)
    if not plan:
        raise HTTPException(
            status_code=422,
            detail={"code": MONITORING_POLICY["source_incomplete_code"], "reason_code": MONITORING_POLICY["invalid_plan_reason_code"]},
        )
    if plan.get("status") != MONITORING_POLICY["approved_status"] or not plan.get(
        "approved_snapshot_hash"
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "code": MONITORING_POLICY["source_incomplete_code"],
                "reason_code": MONITORING_POLICY["plan_not_approved_reason_code"],
            },
        )
    release_id = payload.release_id or plan.get("release_id")
    if release_id and not await test_monitoring_repository.release_exists(release_id, project_id):
        raise HTTPException(status_code=422, detail={"code": MONITORING_POLICY["invalid_release_code"]})
    if payload.idempotency_key:
        existing = await test_monitoring_repository.find_snapshot_by_idempotency(
            project_id, payload.idempotency_key
        )
        if existing:
            if (
                existing.get("test_plan_id") != payload.test_plan_id
                or existing.get("release_id") != release_id
            ):
                raise HTTPException(status_code=409, detail={"code": MONITORING_POLICY["idempotency_conflict_code"]})
            return existing
    timestamp = now()
    sources = await monitoring_sources(project_id, plan, release_id, payload)
    metrics = build_metrics(plan, sources, timestamp)
    evaluations = evaluate_exit_criteria(
        plan.get("quality_targets", []),
        metrics,
        [
            item["_id"]
            for item in sources["runs"]
            if item.get("status") == MONITORING_POLICY["completed_run_status"]
        ],
    )
    blocker_incidents = [
        item
        for item in sources["environment_incidents"]
        if item.get("severity") in MONITORING_POLICY["blocking_incident_severities"]
    ]
    if blocker_incidents:
        evaluations.append(
            {
                **MONITORING_POLICY["environment_incident_gate"],
                "actual": len(blocker_incidents),
                "status": MONITORING_POLICY["failed_status"],
                "overridden": False,
                "evidence_refs": [item["_id"] for item in blocker_incidents],
            }
        )
    source_state = {
        "plan": {
            "id": plan["_id"],
            "revision": plan["revision"],
            "hash": plan["approved_snapshot_hash"],
        },
        "runs": sorted(
            [
                {
                    "id": item["_id"],
                    "revision": item.get("revision"),
                    "scope_hash": item.get("frozen_scope_hash"),
                    "status": item.get("status"),
                    "test_case_version_ids": sorted(item.get("test_case_version_ids", [])),
                    "release_id": item.get("release_id"),
                    "build_id": item.get("build_id"),
                    "environment_id": item.get("environment_id"),
                }
                for item in sources["runs"]
            ],
            key=lambda item: item["id"],
        ),
        "results": sorted(
            [
                {"id": item["_id"], "revision": item.get("revision"), "status": item.get("status")}
                for item in sources["results"]
            ],
            key=lambda item: item["id"],
        ),
        "defects": sorted(
            [
                {
                    "id": item["_id"],
                    "revision": item.get("revision"),
                    "status": item.get("status"),
                    "severity": item.get("severity"),
                }
                for item in sources["defects"]
            ],
            key=lambda item: item["id"],
        ),
        "conditions": sorted(
            [
                {
                    "id": item["_id"],
                    "revision": item.get("revision"),
                    "hash": item.get("snapshot_hash"),
                }
                for item in sources["conditions"]
            ],
            key=lambda item: item["id"],
        ),
        "requirements": sorted(
            item.get("current_version_id")
            for item in sources["requirements"]
            if item.get("current_version_id")
        ),
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
            (
                {"id": item["_id"], "revision": item.get("revision")}
                for item in sources["nfr_plans"]
            ),
            key=lambda item: item["id"],
        ),
        "maintenance": {
            "changed_requirements": sources["changed_requirements"],
            "impact_pending": sources["impact_pending"],
            "proposal_pending": sources["proposal_pending"],
            "stale_testcases": sources["stale_testcases"],
        },
        "environment_incidents": sorted(
            [
                {
                    "id": item["_id"],
                    "revision": item.get("revision"),
                    "status": item.get("status"),
                    "severity": item.get("severity"),
                    "environment_id": item.get("environment_id"),
                    "build_id": item.get("build_id"),
                }
                for item in sources["environment_incidents"]
            ],
            key=lambda item: item["id"],
        ),
    }
    snapshot = {
        "_id": new_id(MONITORING_POLICY["snapshot_id_prefix"]),
        "project_id": project_id,
        "idempotency_key": payload.idempotency_key,
        "test_plan_id": plan["_id"],
        "release_id": release_id,
        "build_id": plan.get("build_id"),
        "snapshot_at": timestamp,
        "plan_revision": plan["revision"],
        "plan_snapshot_hash": plan["approved_snapshot_hash"],
        "planned": {
            "schedule": plan.get("schedule", {}),
            "estimation": plan.get("estimation", {}),
            "quality_targets": plan.get("quality_targets", []),
            "scope_in": plan.get("scope_in", []),
            "scope_out": plan.get("scope_out", []),
        },
        "actual": {
            "run_ids": [item["_id"] for item in sources["runs"]],
            "result_ids": [item["_id"] for item in sources["results"]],
            "defect_ids": [item["_id"] for item in sources["defects"]],
        },
        "metrics": metrics,
        "exit_criteria_evaluation": evaluations,
        "deviations": build_deviations(metrics),
        "risks": [*plan.get("risk_register", []), *payload.risks],
        "blockers": [
            *payload.blockers,
            *[
                {
                    "defect_id": item["_id"],
                    "severity": item.get("severity"),
                    "title": item.get("title"),
                }
                for item in sources["defects"]
                if item.get("status") in OPEN_DEFECT_STATUSES
                and str(item.get("severity", "")).upper()
                == MONITORING_POLICY["blocker_severity"]
            ],
            *[
                {
                    "environment_incident_id": item["_id"],
                    "severity": item.get("severity"),
                    "description": item.get("description"),
                }
                for item in blocker_incidents
            ],
        ],
        "quality_gate_status": quality_gate_status(evaluations),
        "source_fingerprint": source_fingerprint(source_state),
        "source_state": source_state,
        "created_by": user.id,
        "created_at": timestamp,
        "revision": MONITORING_POLICY["initial_revision"],
    }
    gate_evaluation = {
        "_id": new_id(MONITORING_POLICY["gate_evaluation_id_prefix"]),
        "project_id": project_id,
        "test_plan_id": plan["_id"],
        "release_id": release_id,
        "snapshot_id": snapshot["_id"],
        "rules": evaluations,
        "overall_status": snapshot["quality_gate_status"],
        "blocking_reasons": [
            item
            for item in evaluations
            if item.get("status") == MONITORING_POLICY["failed_status"]
        ],
        "warning_reasons": [
            item
            for item in evaluations
            if item.get("status") in MONITORING_POLICY["warning_statuses"]
        ],
        "evaluated_at": timestamp,
        "engine_version": MONITORING_POLICY["gate_engine_version"],
    }
    snapshot["gate_evaluation_id"] = gate_evaluation["_id"]
    try:
        await test_monitoring_repository.insert_snapshot(snapshot)
    except DuplicateKeyError:
        if payload.idempotency_key:
            existing = await test_monitoring_repository.find_snapshot_by_idempotency(
                project_id, payload.idempotency_key
            )
            if (
                existing
                and existing.get("test_plan_id") == payload.test_plan_id
                and existing.get("release_id") == release_id
            ):
                return existing
        raise
    await test_monitoring_repository.insert_gate_evaluation(gate_evaluation)
    await audit(
        user.id,
        MONITORING_POLICY["snapshot_created_event"],
        MONITORING_POLICY["snapshot_entity"],
        snapshot["_id"],
        project_id,
        {
            "source_fingerprint": snapshot["source_fingerprint"],
            "quality_gate_status": snapshot["quality_gate_status"],
        },
    )
    await audit(
        user.id,
        MONITORING_POLICY["criteria_evaluated_event"],
        MONITORING_POLICY["snapshot_entity"],
        snapshot["_id"],
        project_id,
        {
            "criterion_count": len(evaluations),
            "quality_gate_status": snapshot["quality_gate_status"],
        },
    )
    await audit(
        user.id,
        MONITORING_POLICY["gate_evaluated_event"],
        MONITORING_POLICY["gate_entity"],
        gate_evaluation["_id"],
        project_id,
        {"snapshot_id": snapshot["_id"], "overall_status": gate_evaluation["overall_status"]},
    )
    return snapshot


async def effective_snapshot(snapshot):
    overrides = await test_monitoring_repository.list_overrides(
        snapshot["_id"], MONITORING_POLICY["limits"]["overrides"]
    )
    effective = [dict(item) for item in snapshot.get("exit_criteria_evaluation", [])]
    latest = {item["criterion_id"]: item for item in overrides}
    for item in effective:
        override = latest.get(item["criterion_id"])
        if override:
            item.update({"status": override["status"], "overridden": True, "override": override})
    return {
        **snapshot,
        "effective_exit_criteria_evaluation": effective,
        "effective_quality_gate_status": quality_gate_status(effective),
        "overrides": overrides,
    }


async def get_snapshot_for_user(snapshot_id, user):
    snapshot = await test_monitoring_repository.find_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail={"code": MONITORING_POLICY["snapshot_not_found_code"]})
    await get_project(snapshot["project_id"], user, MONITORING_POLICY["read_permission"])
    return await effective_snapshot(snapshot)


async def list_monitoring_snapshots(project_id, test_plan_id, release_id, limit, user):
    await get_project(project_id, user, MONITORING_POLICY["read_permission"])
    return [
        await effective_snapshot(item)
        for item in await test_monitoring_repository.list_snapshots(
            project_id, test_plan_id, release_id, limit
        )
    ]


async def override_exit_criterion(snapshot_id, payload: ExitCriterionOverride, user):
    snapshot = await test_monitoring_repository.find_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail={"code": MONITORING_POLICY["snapshot_not_found_code"]})
    await get_project(snapshot["project_id"], user, MONITORING_POLICY["override_permission"])
    if payload.expected_revision != snapshot.get("revision", 1):
        raise HTTPException(status_code=409, detail={"code": MONITORING_POLICY["revision_conflict_code"]})
    if payload.criterion_id not in {
        item["criterion_id"] for item in snapshot.get("exit_criteria_evaluation", [])
    }:
        raise HTTPException(status_code=404, detail={"code": MONITORING_POLICY["criterion_not_found_code"]})
    value = {
        "_id": new_id(MONITORING_POLICY["override_id_prefix"]),
        "project_id": snapshot["project_id"],
        "snapshot_id": snapshot_id,
        **payload.model_dump(exclude={"expected_revision"}),
        "created_by": user.id,
        "created_at": now(),
    }
    await test_monitoring_repository.insert_override(value)
    await audit(
        user.id,
        MONITORING_POLICY["criterion_overridden_event"],
        MONITORING_POLICY["snapshot_entity"],
        snapshot_id,
        snapshot["project_id"],
        {
            "criterion_id": payload.criterion_id,
            "status": payload.status,
            "reason": payload.reason,
            "override_id": value["_id"],
        },
    )
    return await effective_snapshot(snapshot)


async def create_control_action(project_id, payload: ControlActionCreate, user):
    project = await get_project(project_id, user, MONITORING_POLICY["control_create_permission"])
    snapshot = await test_monitoring_repository.find_snapshot(payload.snapshot_id, project_id)
    if not snapshot:
        raise HTTPException(status_code=422, detail={"code": MONITORING_POLICY["invalid_snapshot_code"]})
    membership = await test_monitoring_repository.find_active_membership(
        project_id, user.id, MONITORING_POLICY["active_membership_status"]
    )
    permissions = (
        permissions_for_role(membership.get("project_role", ""), project.get("settings"))
        if membership
        else set()
    )
    if payload.owner_id != user.id and MONITORING_POLICY["control_assign_permission"] not in permissions:
        raise HTTPException(status_code=403, detail={"code": MONITORING_POLICY["action_assign_denied_code"]})
    if not await test_monitoring_repository.find_active_membership(
        project_id,
        payload.owner_id,
        MONITORING_POLICY["active_membership_status"],
        {"_id": 1},
    ):
        raise HTTPException(status_code=422, detail={"code": MONITORING_POLICY["invalid_action_owner_code"]})
    timestamp = now()
    value = {
        "_id": new_id(MONITORING_POLICY["action_id_prefix"]),
        "project_id": project_id,
        "plan_id": snapshot["test_plan_id"],
        **payload.model_dump(),
        "status": MONITORING_POLICY["initial_action_status"],
        "revision": MONITORING_POLICY["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    await test_monitoring_repository.insert_control_action(value)
    await audit(
        user.id,
        MONITORING_POLICY["action_created_event"],
        MONITORING_POLICY["action_entity"],
        value["_id"],
        project_id,
        {"type": value["type"], "owner_id": value["owner_id"]},
    )
    return value


async def update_control_action(action_id, payload: ControlActionPatch, user):
    action = await test_monitoring_repository.find_control_action(action_id)
    if not action:
        raise HTTPException(status_code=404, detail={"code": MONITORING_POLICY["action_not_found_code"]})
    project = await get_project(
        action["project_id"],
        user,
        MONITORING_POLICY["control_update_permission"],
        assigned_role=MONITORING_POLICY["tester_role"],
        assigned_user_id=action.get("owner_id"),
    )
    actor_membership = await test_monitoring_repository.find_active_membership(
        action["project_id"], user.id, MONITORING_POLICY["active_membership_status"]
    )
    actor_permissions = (
        permissions_for_role(actor_membership.get("project_role", ""), project.get("settings"))
        if actor_membership
        else set()
    )
    if action.get("owner_id") != user.id and MONITORING_POLICY["control_assign_permission"] not in actor_permissions:
        raise HTTPException(status_code=403, detail={"code": MONITORING_POLICY["action_update_denied_code"]})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "owner_id" in changes and changes["owner_id"] != action.get("owner_id"):
        if MONITORING_POLICY["control_assign_permission"] not in actor_permissions:
            raise HTTPException(status_code=403, detail={"code": MONITORING_POLICY["action_assign_denied_code"]})
        if not await test_monitoring_repository.find_active_membership(
            action["project_id"],
            changes["owner_id"],
            MONITORING_POLICY["active_membership_status"],
            {"_id": 1},
        ):
            raise HTTPException(status_code=422, detail={"code": MONITORING_POLICY["invalid_action_owner_code"]})
    allowed = MONITORING_POLICY["action_transitions"]
    if (
        "status" in changes
        and changes["status"] != action["status"]
        and changes["status"] not in allowed[action["status"]]
    ):
        raise HTTPException(
            status_code=409,
            detail={
                "code": MONITORING_POLICY["invalid_transition_code"],
                "from": action["status"],
                "to": changes["status"],
            },
        )
    updated = await test_monitoring_repository.update_control_action(
        action_id,
        action["project_id"],
        payload.expected_revision,
        changes,
        now(),
    )
    if not updated:
        current = await test_monitoring_repository.find_control_action(action_id)
        raise HTTPException(
            status_code=409,
            detail={
                "code": MONITORING_POLICY["revision_conflict_code"],
                "current_revision": current.get("revision") if current else None,
            },
        )
    await audit(
        user.id,
        MONITORING_POLICY["action_updated_event"],
        MONITORING_POLICY["action_entity"],
        action_id,
        action["project_id"],
        {"changed_fields": sorted(changes)},
    )
    return updated


async def list_actions_for_user(project_id, snapshot_id, status, user):
    await get_project(project_id, user, MONITORING_POLICY["read_permission"])
    return await test_monitoring_repository.list_control_actions(
        project_id, snapshot_id, status, MONITORING_POLICY["limits"]["control_actions"]
    )
