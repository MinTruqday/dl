from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.repositories import quality_repository, test_monitoring_repository
from src.domain.test_monitoring import QualityDecisionCreate
from src.services.domain_policy import domain_policy


QUALITY_GATE_POLICY = domain_policy("quality_gate")


async def get_quality_gate(snapshot_id, user):
    snapshot = await test_monitoring_repository.find_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail={"code": QUALITY_GATE_POLICY["snapshot_not_found_code"]})
    await get_project(snapshot["project_id"], user, QUALITY_GATE_POLICY["read_permission"])
    gate = await quality_repository.find_gate(snapshot_id)
    if not gate:
        gate = {
            "_id": snapshot.get("gate_evaluation_id") or f"{QUALITY_GATE_POLICY['evaluation_id_prefix']}-{snapshot_id}",
            "project_id": snapshot["project_id"],
            "test_plan_id": snapshot["test_plan_id"],
            "release_id": snapshot.get("release_id"),
            "snapshot_id": snapshot_id,
            "rules": snapshot.get("exit_criteria_evaluation", []),
            "overall_status": snapshot.get("quality_gate_status", QUALITY_GATE_POLICY["insufficient_data_status"]),
            "blocking_reasons": [
                item
                for item in snapshot.get("exit_criteria_evaluation", [])
                if item.get("status") in QUALITY_GATE_POLICY["blocking_statuses"]
            ],
            "warning_reasons": [
                item
                for item in snapshot.get("exit_criteria_evaluation", [])
                if item.get("status") in QUALITY_GATE_POLICY["warning_statuses"]
            ],
            "evaluated_at": snapshot.get("snapshot_at"),
            "engine_version": QUALITY_GATE_POLICY["engine_version"],
        }
    return gate


async def list_quality_decisions(project_id, release_id, user):
    await get_project(project_id, user, QUALITY_GATE_POLICY["read_permission"])
    query = {"project_id": project_id}
    if release_id:
        query["release_id"] = release_id
    return await quality_repository.list_decisions(query)


async def create_quality_decision(snapshot_id, payload: QualityDecisionCreate, user):
    snapshot = await test_monitoring_repository.find_snapshot(snapshot_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail={"code": QUALITY_GATE_POLICY["snapshot_not_found_code"]})
    permission = (
        QUALITY_GATE_POLICY["accept_risk_permission"]
        if payload.decision == QUALITY_GATE_POLICY["accept_risk_decision"]
        else QUALITY_GATE_POLICY["decide_permission"]
    )
    project = await get_project(snapshot["project_id"], user, permission)
    existing = await quality_repository.find_decision_by_idempotency_key(
        snapshot["project_id"], payload.idempotency_key
    )
    if existing:
        if (
            existing.get("snapshot_id") != snapshot_id
            or existing.get("decision") != payload.decision
        ):
            raise HTTPException(status_code=409, detail={"code": QUALITY_GATE_POLICY["idempotency_conflict_code"]})
        return existing
    gate = await get_quality_gate(snapshot_id, user)
    if payload.decision == QUALITY_GATE_POLICY["approve_release_decision"] and gate.get(
        "overall_status"
    ) == QUALITY_GATE_POLICY["insufficient_data_status"]:
        raise HTTPException(status_code=409, detail={"code": QUALITY_GATE_POLICY["insufficient_data_code"]})
    failed = gate.get("overall_status") in QUALITY_GATE_POLICY["failed_statuses"]
    if payload.decision == QUALITY_GATE_POLICY["approve_release_decision"] and failed:
        if not project.get("settings", {}).get(
            QUALITY_GATE_POLICY["override_setting"],
            QUALITY_GATE_POLICY["override_setting_default"],
        ):
            code = (
                QUALITY_GATE_POLICY["override_not_allowed_code"]
                if payload.override_reason
                else QUALITY_GATE_POLICY["blocked_code"]
            )
            raise HTTPException(status_code=409, detail={"code": code})
        if not payload.override_reason:
            raise HTTPException(
                status_code=422, detail={"code": QUALITY_GATE_POLICY["override_reason_required_code"]}
            )
    if payload.supersedes_decision_id:
        prior = await quality_repository.find_decision(
            payload.supersedes_decision_id, snapshot["project_id"]
        )
        if not prior:
            raise HTTPException(status_code=422, detail={"code": QUALITY_GATE_POLICY["decision_not_found_code"]})
    timestamp = now()
    value = {
        "_id": new_id(QUALITY_GATE_POLICY["decision_id_prefix"]),
        "project_id": snapshot["project_id"],
        "release_id": snapshot.get("release_id"),
        "build_id": snapshot.get("build_id"),
        "snapshot_id": snapshot_id,
        "gate_evaluation_id": gate["_id"],
        **payload.model_dump(),
        "decided_by": user.id,
        "decided_at": timestamp,
        "created_at": timestamp,
    }
    try:
        await quality_repository.insert_decision(value)
    except DuplicateKeyError:
        replay = await quality_repository.find_decision_by_idempotency_key(
            snapshot["project_id"], payload.idempotency_key
        )
        if replay:
            return replay
        raise
    event = (
        QUALITY_GATE_POLICY["risk_accepted_event"]
        if payload.decision == QUALITY_GATE_POLICY["accept_risk_decision"]
        else QUALITY_GATE_POLICY["overridden_event"]
        if payload.override_reason
        else QUALITY_GATE_POLICY["decision_recorded_event"]
    )
    await audit(
        user.id,
        event,
        QUALITY_GATE_POLICY["decision_entity"],
        value["_id"],
        snapshot["project_id"],
        {
            "decision": payload.decision,
            "snapshot_id": snapshot_id,
            "supersedes_decision_id": payload.supersedes_decision_id,
        },
    )
    return value


async def export_quality_gate(snapshot_id, user):
    gate = await get_quality_gate(snapshot_id, user)
    decisions = await list_quality_decisions(gate["project_id"], gate.get("release_id"), user)
    return {
        "gate_evaluation": gate,
        "decision_history": [item for item in decisions if item.get("snapshot_id") == snapshot_id],
        "exported_at": now(),
    }
