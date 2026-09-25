from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.repositories.process_improvement import process_improvement_repository
from src.services.domain_policy import domain_policy
from src.services.statistical_quality import (
    annotate_special_cause,
    compare_statistical_analyses,
    create_statistical_baseline,
    get_statistical_analysis,
    list_statistical_analyses,
    round_measurement,
)


async def require_member(project_id, user_id, code):
    member = await process_improvement_repository.find_active_member(
        project_id,
        user_id,
        domain_policy("process_improvement")["active_membership_status"],
    )
    if not member:
        raise HTTPException(status_code=422, detail={"code": code})


async def get_proposal(proposal_id, user, permission=None):
    policy = domain_policy("process_improvement")
    value = await process_improvement_repository.find_proposal(proposal_id)
    if not value:
        raise HTTPException(
            status_code=404, detail={"code": policy["entity_not_found_code"]}
        )
    await get_project(
        value["project_id"], user, permission or policy["read_permission"]
    )
    return value


async def list_proposals(project_id, user):
    policy = domain_policy("process_improvement")
    await get_project(project_id, user, policy["read_permission"])
    items = await process_improvement_repository.list_proposals(
        project_id, policy["proposal_limit"]
    )
    return {"items": items, "total": len(items)}


async def create_proposal(project_id, payload, user):
    policy = domain_policy("process_improvement")
    await get_project(project_id, user, policy["create_permission"])
    await require_member(
        project_id, payload.owner_id, policy["owner_not_member_code"]
    )
    if payload.idempotency_key:
        existing = await process_improvement_repository.find_by_idempotency(
            project_id, payload.idempotency_key
        )
        if existing:
            if existing.get("observed_problem") != payload.observed_problem:
                raise HTTPException(
                    status_code=409, detail={"code": policy["idempotency_reused_code"]}
                )
            return existing
    timestamp = now()
    value = {
        "_id": new_id(policy["proposal_id_prefix"]),
        "project_id": project_id,
        **payload.model_dump(),
        "lesson_refs": [],
        "causal_analysis_refs": [],
        "baseline_metrics": [],
        "result_metrics": [],
        "decision": None,
        "status": policy["proposed_status"],
        "history": [],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await process_improvement_repository.insert_proposal(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await process_improvement_repository.find_by_idempotency(
                project_id, payload.idempotency_key
            )
        raise
    await audit(
        user.id,
        policy["created_event"],
        policy["entity_type"],
        value["_id"],
        project_id,
        {"source": value["source"], "owner_id": value["owner_id"]},
    )
    return value


async def update_proposal(proposal_id, payload, user):
    policy = domain_policy("process_improvement")
    value = await get_proposal(proposal_id, user, policy["update_permission"])
    if value["status"] != policy["proposed_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["immutable_code"]}
        )
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "owner_id" in changes:
        await require_member(
            value["project_id"], changes["owner_id"], policy["owner_not_member_code"]
        )
    changes["updated_at"] = now()
    updated = await process_improvement_repository.update_proposal(
        proposal_id,
        payload.expected_revision,
        policy["proposed_status"],
        changes,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["revision_conflict_code"]}
        )
    await audit(
        user.id,
        policy["updated_event"],
        policy["entity_type"],
        proposal_id,
        value["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def link_sources(proposal_id, payload, user):
    policy = domain_policy("process_improvement")
    value = await get_proposal(proposal_id, user, policy["update_permission"])
    if value["status"] != policy["proposed_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["immutable_code"]}
        )
    causal = await process_improvement_repository.list_causal_analyses(
        value["project_id"], payload.causal_analysis_refs, policy["source_limit"]
    )
    if len(causal) != len(set(payload.causal_analysis_refs)):
        raise HTTPException(
            status_code=422, detail={"code": policy["rca_not_in_project_code"]}
        )
    reports = await process_improvement_repository.list_completion_lessons(
        value["project_id"], payload.lesson_refs, policy["source_limit"]
    )
    known_lessons = {
        item.get("lesson_id")
        for report in reports
        for item in report.get("lessons_learned", [])
        if item.get("lesson_id")
    }
    if set(payload.lesson_refs) - known_lessons:
        raise HTTPException(
            status_code=422, detail={"code": policy["lesson_not_in_project_code"]}
        )
    updated = await process_improvement_repository.update_proposal(
        proposal_id,
        payload.expected_revision,
        policy["proposed_status"],
        {
            "lesson_refs": sorted(set(payload.lesson_refs)),
            "causal_analysis_refs": sorted(set(payload.causal_analysis_refs)),
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["revision_conflict_code"]}
        )
    await audit(
        user.id,
        policy["sources_linked_event"],
        policy["entity_type"],
        proposal_id,
        value["project_id"],
        {"lesson_refs": payload.lesson_refs, "causal_analysis_refs": payload.causal_analysis_refs},
    )
    return updated


async def metric_snapshots(project_id, references):
    policy = domain_policy("process_improvement")
    items = await process_improvement_repository.list_measurement_snapshots(
        project_id, references, policy["source_limit"]
    )
    if len(items) != len(set(references)):
        raise HTTPException(
            status_code=422, detail={"code": policy["measurement_not_in_project_code"]}
        )
    return [
        {
            "snapshot_id": item["_id"],
            "measurement_key": item.get("measurement_key"),
            "value": item.get("value"),
            "unit": item.get("unit"),
            "measured_at": item.get("measured_at"),
        }
        for item in items
    ]


async def transition_proposal(proposal_id, payload, user, target, permission, event):
    policy = domain_policy("process_improvement")
    value = await get_proposal(proposal_id, user, permission)
    allowed = {tuple(item) for item in policy["allowed_transitions"]}
    if (value["status"], target) not in allowed:
        raise HTTPException(
            status_code=409, detail={"code": policy["invalid_transition_code"]}
        )
    if target == policy["running_status"] and not value.get("baseline_metrics"):
        raise HTTPException(
            status_code=409, detail={"code": policy["baseline_required_code"]}
        )
    timestamp = now()
    entry = {
        "from": value["status"],
        "to": target,
        "actor_id": user.id,
        "note": payload.note,
        "at": timestamp,
    }
    changes = {"status": target, "updated_at": timestamp}
    if target in policy["decision_statuses"]:
        expected = policy["decision_by_status"][target]
        if value.get("decision") != expected:
            raise HTTPException(
                status_code=409, detail={"code": policy["decision_mismatch_code"]}
            )
        changes["decided_by"] = user.id
        changes["decided_at"] = timestamp
    updated = await process_improvement_repository.update_proposal(
        proposal_id,
        payload.expected_revision,
        value["status"],
        changes,
        history_entry=entry,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["revision_conflict_code"]}
        )
    await audit(
        user.id, event, policy["entity_type"], proposal_id, value["project_id"], entry
    )
    return updated


async def record_baseline(proposal_id, payload, user):
    policy = domain_policy("process_improvement")
    value = await get_proposal(proposal_id, user, policy["measure_permission"])
    if value["status"] != policy["approved_experiment_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["not_approved_code"]}
        )
    metrics = await metric_snapshots(
        value["project_id"], payload.measurement_snapshot_refs
    )
    updated = await process_improvement_repository.update_proposal(
        proposal_id,
        payload.expected_revision,
        policy["approved_experiment_status"],
        {
            "baseline_metrics": metrics,
            "baseline_note": payload.note,
            "updated_at": now(),
        },
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["revision_conflict_code"]}
        )
    await audit(
        user.id,
        policy["baseline_recorded_event"],
        policy["entity_type"],
        proposal_id,
        value["project_id"],
        {"snapshot_refs": payload.measurement_snapshot_refs},
    )
    return updated


def compare_metric_results(baseline_metrics, result_metrics):
    def group(items):
        grouped = {}
        for item in items:
            key = item.get("measurement_key") or item.get("snapshot_id")
            grouped.setdefault(key, []).append(item)
        return grouped

    baseline = group(baseline_metrics)
    result = group(result_metrics)
    comparisons = []
    for key in sorted(set(baseline) | set(result)):
        before_items = baseline.get(key, [])
        after_items = result.get(key, [])
        before_values = [item.get("value") for item in before_items]
        after_values = [item.get("value") for item in after_items]
        before_numeric = before_values and all(
            isinstance(item, (int, float)) and not isinstance(item, bool) for item in before_values
        )
        after_numeric = after_values and all(
            isinstance(item, (int, float)) and not isinstance(item, bool) for item in after_values
        )
        before_value = (
            round_measurement(sum(before_values) / len(before_values))
            if before_numeric
            else (before_values[-1] if before_values else None)
        )
        after_value = (
            round_measurement(sum(after_values) / len(after_values))
            if after_numeric
            else (after_values[-1] if after_values else None)
        )
        comparisons.append(
            {
                "measurement_key": key,
                "unit": (after_items or before_items)[-1].get("unit"),
                "baseline_value": before_value,
                "result_value": after_value,
                "delta": round_measurement(after_value - before_value)
                if before_numeric and after_numeric
                else None,
                "changed": before_value != after_value,
                "baseline_snapshot_refs": [item["snapshot_id"] for item in before_items],
                "result_snapshot_refs": [item["snapshot_id"] for item in after_items],
            }
        )
    return comparisons


async def evaluate_proposal(proposal_id, payload, user):
    policy = domain_policy("process_improvement")
    value = await get_proposal(proposal_id, user, policy["evaluate_permission"])
    if value["status"] != policy["running_status"]:
        raise HTTPException(
            status_code=409, detail={"code": policy["not_running_code"]}
        )
    metrics = await metric_snapshots(
        value["project_id"], payload.measurement_snapshot_refs
    )
    comparison = compare_metric_results(value.get("baseline_metrics", []), metrics)
    timestamp = now()
    history = {
        "from": policy["running_status"],
        "to": policy["evaluated_status"],
        "actor_id": user.id,
        "note": payload.note,
        "at": timestamp,
    }
    updated = await process_improvement_repository.update_proposal(
        proposal_id,
        payload.expected_revision,
        policy["running_status"],
        {
            "result_metrics": metrics,
            "result_comparison": comparison,
            "decision": payload.decision,
            "conclusion": payload.conclusion,
            "status": policy["evaluated_status"],
            "evaluated_by": user.id,
            "evaluated_at": timestamp,
            "updated_at": timestamp,
        },
        history_entry=history,
    )
    if not updated:
        raise HTTPException(
            status_code=409, detail={"code": policy["revision_conflict_code"]}
        )
    await audit(
        user.id,
        policy["evaluated_event"],
        policy["entity_type"],
        proposal_id,
        value["project_id"],
        {
            "decision": payload.decision,
            "snapshot_refs": payload.measurement_snapshot_refs,
            "comparison": comparison,
        },
    )
    return updated


class ProcessImprovementService:
    @staticmethod
    async def list(project_id, user):
        return await list_proposals(project_id, user)

    @staticmethod
    async def create(project_id, payload, user):
        return await create_proposal(project_id, payload, user)

    @staticmethod
    async def get(proposal_id, user):
        return await get_proposal(proposal_id, user)

    @staticmethod
    async def update(proposal_id, payload, user):
        return await update_proposal(proposal_id, payload, user)

    @staticmethod
    async def link_sources(proposal_id, payload, user):
        return await link_sources(proposal_id, payload, user)

    @staticmethod
    async def transition_action(proposal_id, payload, user, action):
        transition = domain_policy("process_improvement")["transition_actions"][action]
        return await transition_proposal(
            proposal_id,
            payload,
            user,
            transition["target"],
            transition["permission"],
            transition["event"],
        )

    @staticmethod
    async def record_baseline(proposal_id, payload, user):
        return await record_baseline(proposal_id, payload, user)

    @staticmethod
    async def evaluate(proposal_id, payload, user):
        return await evaluate_proposal(proposal_id, payload, user)

    @staticmethod
    async def list_statistical(project_id, user):
        return await list_statistical_analyses(project_id, user)

    @staticmethod
    async def create_statistical(project_id, payload, user):
        return await create_statistical_baseline(project_id, payload, user)

    @staticmethod
    async def get_statistical(analysis_id, user):
        return await get_statistical_analysis(analysis_id, user)

    @staticmethod
    async def annotate_special_cause(analysis_id, payload, user):
        return await annotate_special_cause(analysis_id, payload, user)

    @staticmethod
    async def compare_statistical(project_id, payload, user):
        return await compare_statistical_analyses(project_id, payload, user)
