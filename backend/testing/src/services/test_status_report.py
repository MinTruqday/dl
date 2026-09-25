import json

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.domain.test_status_report import status_report_hash, status_report_snapshot
from src.repositories.test_status_report import (
    find_ai_result,
    find_build,
    find_monitoring_snapshot,
    find_plan,
    find_report,
    find_report_by_idempotency,
    insert_ai_result,
    insert_report,
    list_control_actions,
    list_reports,
    next_sequence,
    update_report,
)
from src.services.domain_policy import domain_policy
from src.services.design_assistance import ai_contract_metadata, request_design_assistance
from src.services.test_monitoring import effective_snapshot


STATUS_REPORT_POLICY = domain_policy("test_status_report")


def default_recommendation(snapshot):
    policy = STATUS_REPORT_POLICY
    status = snapshot.get("effective_quality_gate_status") or snapshot.get("quality_gate_status")
    if snapshot.get("blockers"):
        return policy["blocked_recommendation"]
    if status == policy["pass_gate_status"]:
        return policy["on_track_recommendation"]
    if status == policy["fail_gate_status"]:
        return policy["not_ready_recommendation"]
    return policy["at_risk_recommendation"]


def text_document(value):
    return (
        {
            "type": "doc",
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": value}]}],
        }
        if value
        else {"type": "doc", "content": []}
    )


def normalized_forecast(value):
    if isinstance(value, str):
        return {
            "expected_completion_at": None,
            "confidence": None,
            "assumptions": [value] if value.strip() else [],
        }
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return value or {"expected_completion_at": None, "confidence": None, "assumptions": []}


def generated_summaries(snapshot):
    metrics = snapshot.get("metrics") or {}
    progress = STATUS_REPORT_POLICY["progress_summary_template"].format(
        executed=metrics.get("executed_test_count", 0),
        planned=metrics.get("planned_test_count", 0),
        percent=metrics.get("execution_percent", 0),
    )
    coverage = (
        STATUS_REPORT_POLICY["coverage_summary_template"].format(
            requirements=metrics.get("requirement_coverage", 0),
            conditions=metrics.get("test_condition_coverage", 0),
            risks=metrics.get("risk_coverage", 0),
        )
    )
    defects = (
        STATUS_REPORT_POLICY["defect_summary_template"].format(
            blocker=metrics.get("open_blocker", 0),
            critical=metrics.get("open_critical", 0),
            reopened=metrics.get("reopened", 0),
        )
    )
    return progress, coverage, defects


async def get_report_for_user(report_id, user, permission=None):
    report = await find_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail={"code": STATUS_REPORT_POLICY["not_found_code"]})
    await get_project(report["project_id"], user, permission or STATUS_REPORT_POLICY["read_permission"])
    return report


async def list_status_reports(project_id, test_plan_id, release_id, status, limit, user):
    await get_project(project_id, user, STATUS_REPORT_POLICY["read_permission"])
    return await list_reports(project_id, test_plan_id, release_id, status, limit)


async def generate_status_report(project_id, payload, user):
    policy = STATUS_REPORT_POLICY
    await get_project(project_id, user, policy["create_permission"])
    if payload.idempotency_key:
        existing = await find_report_by_idempotency(
            project_id, payload.idempotency_key
        )
        if existing:
            if (
                existing.get("snapshot_id") != payload.snapshot_id
                or existing.get("build_id") != payload.build_id
            ):
                raise HTTPException(status_code=409, detail={"code": policy["idempotency_conflict_code"]})
            return existing
    snapshot = await find_monitoring_snapshot(payload.snapshot_id, project_id)
    if not snapshot:
        raise HTTPException(status_code=422, detail={"code": policy["invalid_snapshot_code"]})
    snapshot = await effective_snapshot(snapshot)
    plan = await find_plan(snapshot["test_plan_id"], project_id)
    if not plan:
        raise HTTPException(status_code=422, detail={"code": policy["plan_not_found_code"]})
    build = await find_build(payload.build_id, project_id)
    if not build:
        raise HTTPException(status_code=422, detail={"code": policy["invalid_build_code"]})
    release_id = snapshot.get("release_id")
    if release_id and build.get("release_id") and build["release_id"] != release_id:
        raise HTTPException(status_code=422, detail={"code": policy["build_release_mismatch_code"]})
    actions = await list_control_actions(
        project_id, snapshot["_id"], policy["control_action_limit"]
    )
    progress, coverage, defects = generated_summaries(snapshot)
    recommendation = default_recommendation(snapshot)
    if payload.recommendation and payload.recommendation != recommendation:
        raise HTTPException(
            status_code=422,
            detail={"code": policy["recommendation_mismatch_code"], "expected": recommendation},
        )
    timestamp = now()
    report = {
        "_id": new_id(policy["report_id_prefix"]),
        "project_id": project_id,
        "idempotency_key": payload.idempotency_key,
        "test_plan_id": snapshot["test_plan_id"],
        "strategy_version_id": plan.get("strategy_version_id"),
        "release_id": release_id,
        "build_id": build["_id"],
        "reporting_period": payload.reporting_period.model_dump(),
        "reporting_period_start": payload.reporting_period.start_at,
        "reporting_period_end": payload.reporting_period.end_at,
        "snapshot_id": snapshot["_id"],
        "snapshot_source_fingerprint": snapshot["source_fingerprint"],
        "snapshot_basis": {
            "snapshot_at": snapshot["snapshot_at"],
            "metrics": snapshot.get("metrics", {}),
            "exit_criteria_evaluation": snapshot.get("effective_exit_criteria_evaluation", []),
            "quality_gate_status": snapshot.get(
                "effective_quality_gate_status", snapshot.get("quality_gate_status")
            ),
            "plan_revision": snapshot.get("plan_revision"),
            "plan_snapshot_hash": snapshot.get("plan_snapshot_hash"),
        },
        "executive_summary": payload.executive_summary,
        "executive_summary_doc": text_document(payload.executive_summary),
        "progress_summary": progress,
        "coverage_summary": coverage,
        "defect_summary": defects,
        "maintenance_summary": (snapshot.get("source_state") or {}).get("maintenance", {}),
        "deviations": snapshot.get("deviations", []),
        "blockers": snapshot.get("blockers", []),
        "risks": snapshot.get("risks", []),
        "control_actions": [
            {
                key: action.get(key)
                for key in (
                    "_id",
                    "type",
                    "title",
                    "description",
                    "owner_id",
                    "due_at",
                    "priority",
                    "status",
                    "decision_reason",
                    "evidence_refs",
                )
            }
            for action in actions
        ],
        "control_action_ids": [action["_id"] for action in actions],
        "risk_explanation": "",
        "forecast": normalized_forecast(payload.forecast),
        "recommendation": recommendation,
        "recommendation_narrative": "",
        "distribution": payload.distribution,
        "evidence_refs": payload.evidence_refs,
        "status": policy["draft_status"],
        "sequence": await next_sequence(project_id, snapshot["test_plan_id"], release_id),
        "review_history": [],
        "approval_history": [],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await insert_report(report)
    except DuplicateKeyError:
        if payload.idempotency_key:
            existing = await find_report_by_idempotency(
                project_id, payload.idempotency_key
            )
            if (
                existing
                and existing.get("snapshot_id") == payload.snapshot_id
                and existing.get("build_id") == payload.build_id
            ):
                return existing
        raise
    await audit(
        user.id,
        policy["created_event"],
        policy["report_entity"],
        report["_id"],
        project_id,
        {"snapshot_id": snapshot["_id"], "source_fingerprint": snapshot["source_fingerprint"]},
    )
    return report


async def update_status_report(report_id, payload, user):
    policy = STATUS_REPORT_POLICY
    report = await get_report_for_user(report_id, user, policy["update_permission"])
    if report["status"] != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["immutable_code"]})
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    changes.pop("expected_revision", None)
    if "executive_summary" in changes:
        changes["executive_summary_doc"] = text_document(changes["executive_summary"])
    if "forecast" in changes:
        changes["forecast"] = normalized_forecast(changes["forecast"])
    changes["updated_at"] = now()
    updated = await update_report(
        report_id,
        report["project_id"],
        payload.expected_revision,
        {policy["draft_status"]},
        changes,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["updated_event"],
        policy["report_entity"],
        report_id,
        report["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def generate_status_report_narrative(report_id, payload, user):
    policy = STATUS_REPORT_POLICY
    report = await get_report_for_user(report_id, user, policy["update_permission"])
    if report["status"] != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["immutable_code"]})
    existing = await find_ai_result(
        report["project_id"], payload.idempotency_key
    )
    if existing:
        if (
            existing.get("result_type") != policy["narrative_result_type"]
            or existing.get("subject_id") != report_id
        ):
            raise HTTPException(status_code=409, detail={"code": policy["idempotency_reused_code"]})
        return existing
    narrative_basis = {
        key: report.get(key)
        for key in (
            "snapshot_basis",
            "executive_summary",
            "progress_summary",
            "coverage_summary",
            "defect_summary",
            "deviations",
            "blockers",
            "risks",
            "control_actions",
            "forecast",
            "recommendation",
        )
    }
    narrative_basis["snapshot_basis"] = {
        key: value
        for key, value in (report.get("snapshot_basis") or {}).items()
        if key not in {"plan_snapshot_hash", "source_fingerprint"}
    }
    evidence = [
        {
            "artifact_type": policy["report_artifact_type"],
            "artifact_id": report_id,
            "authority": policy["project_record_authority"],
            "text": json.dumps(narrative_basis, ensure_ascii=False, default=str),
        }
    ]
    instruction = json.dumps(
        {"user_instruction": payload.instruction},
        ensure_ascii=False,
    )
    ai = await request_design_assistance(
        policy["narrative_assistance_type"], report["project_id"], instruction, evidence
    )
    result = {
        "_id": new_id(policy["ai_result_id_prefix"]),
        "project_id": report["project_id"],
        "result_type": policy["narrative_result_type"],
        "subject_id": report_id,
        "candidate_only": True,
        "human_confirmation_required": True,
        "suggestions": ai.get("suggestions", []),
        **ai_contract_metadata(ai),
        "idempotency_key": payload.idempotency_key,
        "created_by": user.id,
        "created_at": now(),
    }
    try:
        await insert_ai_result(result)
    except DuplicateKeyError:
        return await find_ai_result(
            report["project_id"], payload.idempotency_key
        )
    await audit(
        user.id,
        policy["narrative_generated_event"],
        policy["ai_result_entity"],
        result["_id"],
        report["project_id"],
        {"report_id": report_id},
    )
    return result


async def attach_status_report_evidence(report_id, payload, user):
    policy = STATUS_REPORT_POLICY
    report = await get_report_for_user(report_id, user, policy["update_permission"])
    if report["status"] != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": policy["immutable_code"]})
    evidence_refs = list(dict.fromkeys([*report.get("evidence_refs", []), *payload.evidence_refs]))
    updated = await update_report(
        report_id,
        report["project_id"],
        payload.expected_revision,
        {policy["draft_status"]},
        {"evidence_refs": evidence_refs, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["evidence_attached_event"],
        policy["report_entity"],
        report_id,
        report["project_id"],
        {"evidence_refs": payload.evidence_refs},
    )
    return updated


async def transition_status_report(report_id, payload, user, transition_action):
    policy = STATUS_REPORT_POLICY
    transition = policy["transition_actions"][transition_action]
    source = transition["source"]
    target = transition["target"]
    report = await get_report_for_user(report_id, user, transition["permission"])
    timestamp = now()
    event = {"actor_id": user.id, "action": target, "note": payload.note, "at": timestamp}
    changes = {"status": target, "updated_at": timestamp}
    history_field = (
        "approval_history"
        if target in policy["approval_history_statuses"]
        else "review_history"
    )
    changes[history_field] = [*report.get(history_field, []), event]
    if target == policy["review_status"]:
        changes.update({"submitted_by": user.id, "submitted_at": timestamp})
    elif target == policy["draft_status"]:
        changes.update(
            {"change_request": payload.note, "reviewed_by": user.id, "reviewed_at": timestamp}
        )
    elif target == policy["approved_status"]:
        approved_snapshot = status_report_snapshot(report)
        changes.update(
            {
                "approved_by": user.id,
                "approved_at": timestamp,
                "approved_snapshot": approved_snapshot,
                "approved_snapshot_hash": status_report_hash(report),
            }
        )
    elif target == policy["published_status"]:
        changes.update({"published_by": user.id, "published_at": timestamp})
    updated = await update_report(
        report_id, report["project_id"], payload.expected_revision, {source}, changes
    )
    if not updated:
        raise HTTPException(
            status_code=409,
            detail={"code": policy["transition_conflict_code"], "expected_status": source},
        )
    await audit(
        user.id,
        transition["event"],
        policy["report_entity"],
        report_id,
        report["project_id"],
        {"from": source, "to": target, "note": payload.note},
    )
    return updated


async def compare_status_reports(report_id, other_report_id, user):
    left = await get_report_for_user(report_id, user)
    right = await find_report(other_report_id, left["project_id"])
    if not right:
        raise HTTPException(
            status_code=404, detail={"code": STATUS_REPORT_POLICY["compare_target_not_found_code"]}
        )
    fields = (
        "executive_summary",
        "progress_summary",
        "coverage_summary",
        "defect_summary",
        "deviations",
        "blockers",
        "risks",
        "control_actions",
        "forecast",
        "recommendation",
        "distribution",
        "status",
    )
    changes = [
        {"field": field, "from": left.get(field), "to": right.get(field)}
        for field in fields
        if left.get(field) != right.get(field)
    ]
    return {
        "from_report_id": report_id,
        "to_report_id": other_report_id,
        "from_sequence": left.get("sequence"),
        "to_sequence": right.get("sequence"),
        "changes": changes,
    }
