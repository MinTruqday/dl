from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.domain.test_completion import completion_hash, completion_snapshot
from src.repositories.test_completion import (
    find_active_member,
    find_completion_by_idempotency_key,
    find_monitoring_snapshot,
    find_test_plan,
    insert_completion,
    maintenance_summary,
    next_completion_sequence,
    update_completion,
)
from src.services.exit_criteria import quality_gate_status
from src.services.domain_policy import domain_policy
from src.services.test_completion_assistance import completion_ai_result
from src.services.test_completion_policy import (
    default_completion_recommendation,
    reevaluate_completion_exit_criteria,
    validate_completion_readiness,
)
from src.services.test_completion_query import (
    get_completion_for_user,
    list_completion_reports,
    validate_people,
)
from src.services.test_completion_sources import completion_sources, handover_records
from src.services.test_completion_updates import (
    add_completion_lesson,
    add_completion_residual_risk,
    manage_completion_handover,
)

COMPLETION_POLICY = domain_policy("completion")
OPEN_DEFECT_STATUSES = set(COMPLETION_POLICY["open_defect_statuses"])

__all__ = [
    "add_completion_lesson",
    "add_completion_residual_risk",
    "list_completion_reports",
    "manage_completion_handover",
]


async def create_completion_report(project_id, payload, user):
    policy = COMPLETION_POLICY
    statuses = policy["statuses"]
    types = policy["artifact_types"]
    codes = policy["error_codes"]
    await get_project(project_id, user, policy["permissions"]["create"])
    if payload.idempotency_key:
        existing = await find_completion_by_idempotency_key(
            project_id, payload.idempotency_key
        )
        if existing:
            if (
                existing.get("monitoring_snapshot_id") != payload.snapshot_id
                or existing.get("build_id") != payload.build_id
            ):
                raise HTTPException(status_code=409, detail={"code": codes["idempotency_reused"]})
            return existing
    snapshot = await find_monitoring_snapshot(project_id, payload.snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=422, detail={"code": codes["snapshot_invalid"]})
    plan = await find_test_plan(project_id, snapshot["test_plan_id"])
    if (
        not plan
        or plan.get("status") != statuses["approved"]
        or plan.get("approved_snapshot_hash") != snapshot.get("plan_snapshot_hash")
    ):
        raise HTTPException(status_code=409, detail={"code": codes["plan_snapshot_invalid"]})
    sources = await completion_sources(project_id, snapshot, plan, payload.build_id)
    (
        release,
        build,
        strategy,
        runs,
        results,
        defects,
        environments,
        data_sets,
        automation,
        status_reports,
        archived_testcases,
        archived_documents,
    ) = sources
    residual_risks = [item.model_dump() for item in payload.residual_risks]
    improvement_actions = [item.model_dump() for item in payload.improvement_actions]
    lessons_learned = [
        {
            **item.model_dump(),
            "lesson_id": item.lesson_id or new_id(policy["id_prefixes"]["lesson"]),
        }
        for item in payload.lessons_learned
    ]
    supplied_handover = [item.model_dump() for item in payload.testware_handover]
    supplied_unexecuted = [item.model_dump() for item in payload.unexecuted_scope]
    await validate_people(
        project_id,
        [
            *[item["owner_id"] for item in residual_risks],
            *[item.get("accepted_by") for item in residual_risks],
            *[item["owner_id"] for item in improvement_actions],
            *[item.get("owner_id") for item in lessons_learned],
        ],
    )
    if any(item.get("treatment") != statuses["pending"] for item in residual_risks):
        raise HTTPException(
            status_code=422, detail={"code": codes["risk_decision_endpoint_required"]}
        )
    completed_run_ids = sorted(
        item["_id"] for item in runs if item.get("status") == statuses["completed"]
    )
    metrics = snapshot.get("metrics") or {}
    exit_evaluation = await reevaluate_completion_exit_criteria(plan, snapshot, completed_run_ids)
    gate = quality_gate_status(exit_evaluation)
    open_defects = [item for item in defects if item.get("status") in OPEN_DEFECT_STATUSES]
    generated_unresolved = [
        {
            "type": types["defect"],
            "defect_id": item["_id"],
            "title": item.get("title"),
            "severity": item.get("severity"),
            "status": item.get("status"),
            "owner_id": item.get("assignee"),
        }
        for item in open_defects
    ]
    omitted = [
        {
            "item_id": result["_id"],
            "item_type": types["test_result"],
            "reason": result.get("reason") or result.get("notes") or "",
            "source_refs": [
                value
                for value in (result.get("test_run_id"), result.get("test_case_version_id"))
                if value
            ],
        }
        for result in results
        if result.get("status") in set(policy["result_omission_statuses"])
    ]
    unexecuted_scope = [*omitted, *supplied_unexecuted]
    unresolved_items = [*generated_unresolved, *payload.unresolved_items]
    scope_runs = [
        {
            "run_id": item["_id"],
            "revision": item.get("revision"),
            "status": item.get("status"),
            "mandatory": item.get("mandatory", item.get("is_mandatory", True)),
            "frozen_scope_hash": item.get("frozen_scope_hash"),
            "test_case_version_ids": item.get("test_case_version_ids", []),
            "release_id": item.get("release_id"),
            "build_id": item.get("build_id"),
            "environment_id": item.get("environment_id"),
        }
        for item in runs
    ]
    testware = [
        *handover_records(
            types["test_case_version"],
            (snapshot.get("source_state") or {}).get("test_case_versions", []),
            "test-case-versions",
        ),
        *handover_records(types["data_set"], data_sets, "data-sets"),
        *handover_records(types["automation_script"], automation, "automation-scripts"),
        *handover_records(types["status_report"], status_reports, "status-reports"),
        *supplied_handover,
    ]
    archived = [
        {"type": types["test_case"], "items": archived_testcases},
        {"type": types["requirement_document"], "items": archived_documents},
        *payload.archived_artifacts,
    ]
    environment_closure = [
        {
            "environment_id": item["_id"],
            "name": item.get("name"),
            "availability": item.get("availability"),
            "status": item.get("status"),
            "revision": item.get("revision"),
        }
        for item in environments
    ] + payload.environment_closure
    recommendation = default_completion_recommendation(gate, unresolved_items, residual_risks)
    if payload.recommendation and payload.recommendation != recommendation:
        raise HTTPException(
            status_code=422,
            detail={"code": codes["recommendation_mismatch"], "expected": recommendation},
        )
    source_filters = policy["source_filters"]
    maintenance = await maintenance_summary(
        project_id,
        source_filters["maintenance_pending_status"],
        source_filters["maintenance_applied_statuses"],
    )
    timestamp = now()
    sequence = await next_completion_sequence(project_id, release["_id"])
    report = {
        "_id": new_id(policy["id_prefixes"]["report"]),
        "project_id": project_id,
        "completion_key": f"{policy['id_prefixes']['report_key']}{sequence:04d}",
        "idempotency_key": payload.idempotency_key,
        "test_plan_id": plan["_id"],
        "release_id": release["_id"],
        "build_id": build["_id"],
        "build_ids": [build["_id"]],
        "strategy_version_id": strategy["_id"],
        "strategy_snapshot_hash": strategy["snapshot_hash"],
        "monitoring_snapshot_id": snapshot["_id"],
        "final_snapshot_id": snapshot["_id"],
        "scope_snapshot": {
            "plan_revision": snapshot.get("plan_revision"),
            "plan_snapshot_hash": snapshot.get("plan_snapshot_hash"),
            "scope_in": (plan.get("approved_snapshot") or {}).get("scope_in", []),
            "scope_out": (plan.get("approved_snapshot") or {}).get("scope_out", []),
            "runs": scope_runs,
            "source_fingerprint": snapshot.get("source_fingerprint"),
        },
        "completed_run_ids": completed_run_ids,
        "execution_summary": {
            key: metrics.get(key)
            for key in (
                "planned_test_count",
                "executed_test_count",
                "execution_percent",
                "pass",
                "fail",
                "blocked",
                "skipped",
                "not_applicable",
                "pass_rate",
            )
        },
        "coverage_summary": {
            key: metrics.get(key)
            for key in (
                "requirement_coverage",
                "acceptance_criteria_coverage",
                "test_condition_coverage",
                "risk_coverage",
                "api_coverage",
                "nfr_coverage",
            )
        },
        "defect_summary": {
            "total": len(defects),
            "open": len(open_defects),
            "open_blocker": metrics.get("open_blocker", 0),
            "open_critical": metrics.get("open_critical", 0),
            "resolved": metrics.get("resolved", 0),
            "reopened": metrics.get("reopened", 0),
        },
        "maintenance_summary": maintenance,
        "unexecuted_scope": unexecuted_scope,
        "unresolved_items": unresolved_items,
        "residual_risks": residual_risks,
        "exit_criteria_evaluation": exit_evaluation,
        "exit_criteria_evaluations": exit_evaluation,
        "quality_gate_status": gate,
        "deviations": [*snapshot.get("deviations", []), *payload.deviations],
        "testware_handover": testware,
        "archived_artifacts": archived,
        "environment_closure": environment_closure,
        "lessons_learned": lessons_learned,
        "improvement_actions": improvement_actions,
        "recommendation": recommendation,
        "executive_summary": "",
        "closure_summary": "",
        "residual_risk_summary": "",
        "recommendation_rationale": "",
        "sign_offs": [],
        "status": statuses["draft"],
        "sequence": sequence,
        "revision": 1,
        "review_history": [],
        "approval_history": [],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await insert_completion(report)
    except DuplicateKeyError:
        existing = (
            await find_completion_by_idempotency_key(project_id, payload.idempotency_key)
            if payload.idempotency_key
            else None
        )
        if not existing:
            raise
        if (
            existing.get("monitoring_snapshot_id") != payload.snapshot_id
            or existing.get("build_id") != payload.build_id
        ):
            raise HTTPException(status_code=409, detail={"code": codes["idempotency_reused"]})
        return existing
    await audit(
        user.id,
        policy["events"]["created"],
        policy["entity_type"],
        report["_id"],
        project_id,
        {"release_id": release["_id"], "snapshot_id": snapshot["_id"], "quality_gate_status": gate},
    )
    return report


async def update_completion_report(report_id, payload, user):
    policy = COMPLETION_POLICY
    statuses = policy["statuses"]
    types = policy["artifact_types"]
    codes = policy["error_codes"]
    report = await get_completion_for_user(report_id, user, policy["permissions"]["update"])
    if report["status"] != statuses["draft"]:
        raise HTTPException(status_code=409, detail={"code": codes["immutable"]})
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    changes.pop("expected_revision", None)
    if "unresolved_items" in changes:
        generated = [
            item
            for item in report.get("unresolved_items", [])
            if isinstance(item, dict) and item.get("type") == types["defect"]
        ]
        identities = {
            (item.get("defect_id"), item.get("type"))
            for item in changes["unresolved_items"]
            if isinstance(item, dict)
        }
        if any((item.get("defect_id"), item.get("type")) not in identities for item in generated):
            raise HTTPException(
                status_code=422, detail={"code": codes["generated_fact_immutable"]}
            )
    if "unexecuted_scope" in changes:
        existing = {
            item.get("item_id")
            for item in report.get("unexecuted_scope", [])
            if item.get("item_type") == types["test_result"]
        }
        incoming = {
            item.get("item_id")
            for item in changes["unexecuted_scope"]
            if item.get("item_type") == types["test_result"]
        }
        if not existing <= incoming:
            raise HTTPException(
                status_code=422, detail={"code": codes["generated_fact_immutable"]}
            )
    if (
        "residual_risks" in changes
        or "improvement_actions" in changes
        or "lessons_learned" in changes
    ):
        await validate_people(
            report["project_id"],
            [
                *[item["owner_id"] for item in changes.get("residual_risks", [])],
                *[item.get("accepted_by") for item in changes.get("residual_risks", [])],
                *[item["owner_id"] for item in changes.get("improvement_actions", [])],
                *[item.get("owner_id") for item in changes.get("lessons_learned", [])],
            ],
        )
    if "residual_risks" in changes:
        existing_risks = {item.get("risk_id"): item for item in report.get("residual_risks", [])}
        incoming_risk_ids = {item.get("risk_id") for item in changes["residual_risks"]}
        if (
            not incoming_risk_ids <= set(existing_risks)
            or not set(existing_risks) <= incoming_risk_ids
        ):
            await get_project(report["project_id"], user, policy["permissions"]["risk_manage"])
        for item in changes["residual_risks"]:
            previous = existing_risks.get(item.get("risk_id")) or {}
            decision = (
                item.get("treatment"),
                item.get("acceptance_reason"),
                item.get("accepted_by"),
            )
            previous_decision = (
                previous.get("treatment", previous.get("acceptance")),
                previous.get("acceptance_reason"),
                previous.get("accepted_by"),
            )
            if item.get("treatment") != statuses["pending"] and decision != previous_decision:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "code": codes["risk_decision_endpoint_required"],
                        "risk_id": item.get("risk_id"),
                    },
                )
    if "lessons_learned" in changes and len(changes["lessons_learned"]) > len(
        report.get("lessons_learned", [])
    ):
        await get_project(report["project_id"], user, policy["permissions"]["lesson_create"])
    if "testware_handover" in changes:
        await get_project(report["project_id"], user, policy["permissions"]["handover_manage"])
    changes["updated_at"] = now()
    updated = await update_completion(
        report_id,
        report["project_id"],
        payload.expected_revision,
        {statuses["draft"]},
        changes,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["updated"],
        policy["entity_type"],
        report_id,
        report["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def generate_completion_narrative(report_id, payload, user):
    policy = COMPLETION_POLICY
    action = policy["ai_actions"]["narrative"]
    report = await get_completion_for_user(report_id, user, policy["permissions"]["update"])
    return await completion_ai_result(
        report,
        payload,
        user,
        action["task"],
        action["result_type"],
    )


async def cluster_completion_lessons(report_id, payload, user):
    policy = COMPLETION_POLICY
    action = policy["ai_actions"]["lesson_clusters"]
    report = await get_completion_for_user(report_id, user, policy["permissions"]["update"])
    if not report.get("lessons_learned"):
        raise HTTPException(
            status_code=422,
            detail={"code": policy["error_codes"]["lessons_required"]},
        )
    return await completion_ai_result(
        report,
        payload,
        user,
        action["task"],
        action["result_type"],
    )


async def decide_residual_risk(report_id, risk_id, payload, user):
    policy = COMPLETION_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    report = await get_completion_for_user(report_id, user, policy["permissions"]["review"])
    mutable_statuses = {statuses["draft"], statuses["in_review"]}
    if report["status"] not in mutable_statuses:
        raise HTTPException(status_code=409, detail={"code": codes["immutable"]})
    membership = await find_active_member(
        report["project_id"],
        user.id,
        policy["source_filters"]["active_membership_status"],
    )
    risks = [dict(item) for item in report.get("residual_risks", [])]
    risk = next((item for item in risks if item.get("risk_id") == risk_id), None)
    if not risk:
        raise HTTPException(status_code=404, detail={"code": codes["risk_not_found"]})
    if (
        risk.get("owner_id") != user.id
        and (membership or {}).get("project_role") not in set(policy["qa_roles"])
    ):
        raise HTTPException(status_code=403, detail={"code": codes["risk_decision_denied"]})
    risk.update(
        {
            "treatment": payload.acceptance,
            "acceptance": payload.acceptance,
            "acceptance_reason": payload.reason,
            "accepted_by": user.id,
            "accepted_at": now(),
            "status": statuses["closed"]
            if payload.acceptance in set(policy["risk_closed_decisions"])
            else statuses["monitoring"],
        }
    )
    updated = await update_completion(
        report_id,
        report["project_id"],
        payload.expected_revision,
        mutable_statuses,
        {"residual_risks": risks, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    event = (
        policy["events"]["risk_accepted"]
        if payload.acceptance == policy["risk_closed_decisions"][0]
        else policy["events"]["risk_decided"]
    )
    await audit(
        user.id,
        event,
        policy["entity_type"],
        report_id,
        report["project_id"],
        {"risk_id": risk_id, "acceptance": payload.acceptance, "reason": payload.reason},
    )
    return updated


async def sign_off_completion(report_id, payload, user):
    policy = COMPLETION_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    report = await get_completion_for_user(report_id, user, policy["permissions"]["review"])
    if report["status"] != statuses["in_review"]:
        raise HTTPException(status_code=409, detail={"code": codes["sign_off_state_invalid"]})
    membership = await find_active_member(
        report["project_id"],
        user.id,
        policy["source_filters"]["active_membership_status"],
    )
    if not membership:
        raise HTTPException(status_code=403, detail={"code": codes["membership_required"]})
    sign_offs = [item for item in report.get("sign_offs", []) if item.get("user_id") != user.id]
    sign_offs.append(
        {
            "user_id": user.id,
            "role": membership.get("project_role"),
            "decision": payload.decision,
            "note": payload.note,
            "at": now(),
        }
    )
    updated = await update_completion(
        report_id,
        report["project_id"],
        payload.expected_revision,
        {statuses["in_review"]},
        {"sign_offs": sign_offs, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["signed_off"],
        policy["entity_type"],
        report_id,
        report["project_id"],
        {"decision": payload.decision, "role": membership.get("project_role")},
    )
    return updated


async def transition_completion(report_id, payload, user, transition_action):
    policy = COMPLETION_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    transition = policy["transitions"][transition_action]
    source = transition["source"]
    target = transition["target"]
    report = await get_completion_for_user(report_id, user, transition["permission"])
    if target == statuses["approved"]:
        await validate_completion_readiness(report)
        qa_approved = any(
            item.get("role") == policy["qa_sign_off_role"]
            and item.get("decision") == policy["approve_decision"]
            for item in report.get("sign_offs", [])
        )
        if not qa_approved:
            raise HTTPException(status_code=409, detail={"code": codes["qa_sign_off_required"]})
        if any(
            item.get("treatment", item.get("acceptance")) == statuses["pending"]
            for item in report.get("residual_risks", [])
        ):
            raise HTTPException(
                status_code=409, detail={"code": codes["risk_acceptance_required"]}
            )
        if any(
            item.get("decision") == policy["reject_decision"]
            for item in report.get("sign_offs", [])
        ):
            raise HTTPException(status_code=409, detail={"code": codes["rejection_unresolved"]})
    timestamp = now()
    event = {"actor_id": user.id, "action": target, "note": payload.note, "at": timestamp}
    history_field = (
        "approval_history"
        if target in set(policy["history_statuses"])
        else "review_history"
    )
    changes = {
        "status": target,
        "updated_at": timestamp,
        history_field: [*report.get(history_field, []), event],
    }
    if target == statuses["in_review"]:
        changes.update({"submitted_by": user.id, "submitted_at": timestamp})
    elif target == statuses["draft"]:
        changes.update(
            {
                "reviewed_by": user.id,
                "reviewed_at": timestamp,
                "change_request": payload.note,
                "sign_offs": [],
            }
        )
    elif target == statuses["approved"]:
        changes.update(
            {
                "approved_by": user.id,
                "approved_at": timestamp,
                "approved_snapshot": completion_snapshot(report),
                "approved_snapshot_hash": completion_hash(report),
            }
        )
    elif target == statuses["closed"]:
        changes.update({"closed_by": user.id, "closed_at": timestamp})
    updated = await update_completion(
        report_id, report["project_id"], payload.expected_revision, {source}, changes
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": codes["transition_conflict"], "expected_status": source},
        )
    await audit(
        user.id,
        transition["event"],
        policy["entity_type"],
        report_id,
        report["project_id"],
        {"from": source, "to": target, "note": payload.note},
    )
    return updated
