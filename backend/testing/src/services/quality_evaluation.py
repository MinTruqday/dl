from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.repositories import quality_repository
from src.services.domain_policy import domain_policy
from src.services.test_monitoring import effective_snapshot


QUALITY_POLICY = domain_policy("quality_evaluation")


def system_recommendation(gate_status, critical_risks):
    policy = QUALITY_POLICY
    if gate_status == policy["failed_gate_status"]:
        return policy["recommendations"]["failed"]
    if gate_status in policy["insufficient_gate_statuses"]:
        return policy["recommendations"]["insufficient"]
    if gate_status == policy["warning_gate_status"]:
        return policy["recommendations"]["warning"]
    return (
        policy["recommendations"]["risk"]
        if critical_risks
        else policy["recommendations"]["pass"]
    )


def evaluate_quality_objectives(objectives, snapshots):
    policy = QUALITY_POLICY
    measurements = {}
    for snapshot in sorted(
        snapshots,
        key=lambda item: str(item.get("measured_at") or item.get("created_at") or ""),
        reverse=True,
    ):
        measurements.setdefault(snapshot.get("measurement_key"), snapshot)
    results = []
    for objective in objectives:
        key = objective.get("key") or objective.get("metric")
        target = objective.get("target")
        snapshot = measurements.get(key)
        actual = snapshot.get("value") if snapshot else None
        if (
            not isinstance(actual, (int, float))
            or isinstance(actual, bool)
            or not isinstance(target, (int, float))
            or isinstance(target, bool)
        ):
            status = policy["insufficient_status"]
        elif key in policy["lower_is_better"]:
            status = policy["pass_status"] if actual <= target else policy["fail_status"]
        else:
            status = policy["pass_status"] if actual >= target else policy["fail_status"]
        results.append(
            {
                **objective,
                "measurement_snapshot_id": snapshot.get("_id") if snapshot else None,
                "actual": actual,
                "status": status,
            }
        )
    return results


def rationale_document(value):
    return {
        "type": "doc",
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": value}]}],
    }


async def get_evaluation(evaluation_id, user, permission=None):
    policy = QUALITY_POLICY
    value = await quality_repository.find_evaluation(evaluation_id)
    if not value:
        raise HTTPException(
            status_code=404, detail={"code": policy["error_codes"]["not_found"]}
        )
    await get_project(
        value["project_id"], user, permission or policy["permissions"]["read"]
    )
    return value


async def list_evaluations(project_id, release_id, user):
    policy = QUALITY_POLICY
    await get_project(project_id, user, policy["permissions"]["read"])
    query = {"project_id": project_id}
    if release_id:
        query["release_id"] = release_id
    items = await quality_repository.list_evaluations(
        query, policy["list_limit"]
    )
    return {"items": items, "total": len(items)}


async def create_evaluation(project_id, payload, user):
    policy = QUALITY_POLICY
    codes = policy["error_codes"]
    await get_project(project_id, user, policy["permissions"]["create"])
    if payload.idempotency_key:
        existing = await quality_repository.find_evaluation_by_idempotency_key(
            project_id, payload.idempotency_key
        )
        if existing:
            if (
                existing.get("release_id") != payload.release_id
                or existing.get("build_id") != payload.build_id
            ):
                raise HTTPException(
                    status_code=409, detail={"code": codes["idempotency_reused"]}
                )
            return existing
    release = await quality_repository.find_release(payload.release_id, project_id)
    build = await quality_repository.find_build(payload.build_id, project_id)
    monitoring = await quality_repository.find_monitoring_snapshot(
        payload.monitoring_snapshot_id, project_id, payload.release_id
    )
    snapshots = await quality_repository.list_measurement_snapshots(
        payload.measurement_snapshot_refs, project_id, policy["measurement_limit"]
    )
    if (
        not release
        or not build
        or not monitoring
        or len(snapshots) != len(set(payload.measurement_snapshot_refs))
    ):
        raise HTTPException(
            status_code=422, detail={"code": codes["source_not_in_project"]}
        )
    if any(item.get("release_id") not in {None, payload.release_id} for item in snapshots):
        raise HTTPException(
            status_code=422, detail={"code": codes["measurement_release_mismatch"]}
        )
    monitoring = await effective_snapshot(monitoring)
    plan = await quality_repository.find_test_plan(
        monitoring["test_plan_id"], project_id
    )
    strategy = await quality_repository.find_strategy(
        (plan or {}).get("strategy_version_id"), project_id
    )
    gate = await quality_repository.find_gate_for_project(
        monitoring["_id"], project_id
    )
    if not plan or not strategy or not gate:
        raise HTTPException(
            status_code=422, detail={"code": codes["source_incomplete"]}
        )
    unresolved = await quality_repository.list_unresolved_defects(
        project_id,
        payload.release_id,
        policy["resolved_defect_statuses"],
        policy["defect_limit"],
    )
    gate_status = monitoring.get(
        "effective_quality_gate_status", monitoring.get("quality_gate_status")
    )
    recommendation = system_recommendation(gate_status, payload.critical_risks)
    if payload.recommendation and payload.recommendation != recommendation:
        raise HTTPException(
            status_code=422,
            detail={"code": codes["recommendation_mismatch"], "expected": recommendation},
        )
    human_decision = await quality_repository.find_latest_decision(
        monitoring["_id"], project_id
    )
    timestamp = now()
    value = {
        "_id": new_id(policy["evaluation_id_prefix"]),
        "project_id": project_id,
        **payload.model_dump(exclude={"recommendation"}),
        "snapshot_id": monitoring["_id"],
        "strategy_version_id": strategy["_id"],
        "gate_evaluation_id": gate["_id"],
        "measurement_snapshots": snapshots,
        "quality_objective_results": evaluate_quality_objectives(
            strategy.get("quality_objectives", []), snapshots
        ),
        "exit_criteria_results": monitoring.get("effective_exit_criteria_evaluation", []),
        "exit_criteria_snapshot": monitoring.get("effective_exit_criteria_evaluation", []),
        "quality_gate_status": gate_status,
        "system_recommendation": recommendation,
        "recommendation": recommendation,
        "rationale_doc": rationale_document(payload.rationale),
        "human_decision": human_decision,
        "quality_decision_id": human_decision.get("_id") if human_decision else None,
        "unresolved_defects": unresolved,
        "waivers": [],
        "reviewed_by": [],
        "approved_by": None,
        "status": policy["draft_status"],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await quality_repository.insert_evaluation(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await quality_repository.find_evaluation_by_idempotency_key(
                project_id, payload.idempotency_key
            )
        raise
    await audit(
        user.id,
        policy["events"]["created"],
        policy["entity_type"],
        value["_id"],
        project_id,
        {
            "release_id": payload.release_id,
            "recommendation": recommendation,
            "measurement_snapshot_refs": payload.measurement_snapshot_refs,
        },
    )
    return value


async def update_evaluation(evaluation_id, payload, user):
    policy = QUALITY_POLICY
    codes = policy["error_codes"]
    value = await get_evaluation(evaluation_id, user, policy["permissions"]["create"])
    if value["status"] != policy["draft_status"]:
        raise HTTPException(status_code=409, detail={"code": codes["immutable"]})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "recommendation" in changes and changes["recommendation"] != value.get(
        "system_recommendation", value.get("recommendation")
    ):
        raise HTTPException(
            status_code=409, detail={"code": codes["recommendation_immutable"]}
        )
    changes.pop("recommendation", None)
    if "rationale" in changes:
        changes["rationale_doc"] = rationale_document(changes["rationale"])
    changes["updated_at"] = now()
    updated = await quality_repository.update_evaluation(
        {
            "_id": evaluation_id,
            "revision": payload.expected_revision,
            "status": policy["draft_status"],
        },
        {"$set": changes, "$inc": {"revision": 1}},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["updated"],
        policy["entity_type"],
        evaluation_id,
        value["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def submit_evaluation(evaluation_id, payload, user):
    policy = QUALITY_POLICY
    codes = policy["error_codes"]
    value = await get_evaluation(evaluation_id, user, policy["permissions"]["review"])
    if value["status"] != policy["draft_status"]:
        raise HTTPException(
            status_code=409, detail={"code": codes["invalid_transition"]}
        )
    updated = await quality_repository.update_evaluation(
        {
            "_id": evaluation_id,
            "revision": payload.expected_revision,
            "status": policy["draft_status"],
        },
        {
            "$set": {
                "status": policy["review_status"],
                "submitted_by": user.id,
                "submitted_at": now(),
                "submission_note": payload.note,
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["submitted"],
        policy["entity_type"],
        evaluation_id,
        value["project_id"],
        {"note": payload.note},
    )
    return updated


async def review_evaluation(evaluation_id, payload, user):
    policy = QUALITY_POLICY
    codes = policy["error_codes"]
    value = await get_evaluation(evaluation_id, user, policy["permissions"]["review"])
    if value["status"] != policy["review_status"]:
        raise HTTPException(status_code=409, detail={"code": codes["not_in_review"]})
    history = [
        *value.get("reviewed_by", []),
        {"actor_id": user.id, "decision": payload.decision, "note": payload.note, "at": now()},
    ]
    changes = {"reviewed_by": history, "updated_at": now()}
    if payload.decision == policy["request_changes_decision"]:
        changes["status"] = policy["draft_status"]
    updated = await quality_repository.update_evaluation(
        {
            "_id": evaluation_id,
            "revision": payload.expected_revision,
            "status": policy["review_status"],
        },
        {"$set": changes, "$inc": {"revision": 1}},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["reviewed"],
        policy["entity_type"],
        evaluation_id,
        value["project_id"],
        {"decision": payload.decision},
    )
    return updated


async def add_waiver(evaluation_id, payload, user):
    policy = QUALITY_POLICY
    codes = policy["error_codes"]
    value = await get_evaluation(evaluation_id, user, policy["permissions"]["create"])
    if value["status"] not in policy["editable_statuses"]:
        raise HTTPException(status_code=409, detail={"code": codes["immutable"]})
    if payload.expiry_at <= now():
        raise HTTPException(status_code=422, detail={"code": codes["waiver_expiry_future"]})
    if not await quality_repository.find_active_member(
        value["project_id"], payload.owner_id, policy["active_membership_status"]
    ):
        raise HTTPException(
            status_code=422, detail={"code": codes["waiver_owner_not_member"]}
        )
    expected_revision = payload.expected_revision or value["revision"]
    waiver = {
        "waiver_id": new_id(policy["waiver_id_prefix"]),
        **payload.model_dump(exclude={"expected_revision"}),
        "status": policy["pending_status"],
        "approved_by": None,
        "created_by": user.id,
        "created_at": now(),
    }
    updated = await quality_repository.update_evaluation(
        {
            "_id": evaluation_id,
            "revision": expected_revision,
            "status": {"$in": policy["editable_statuses"]},
        },
        {"$push": {"waivers": waiver}, "$set": {"updated_at": now()}, "$inc": {"revision": 1}},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["stale_revision"]})
    await audit(
        user.id,
        policy["events"]["waiver_created"],
        policy["entity_type"],
        evaluation_id,
        value["project_id"],
        {"waiver_id": waiver["waiver_id"], "risk": waiver["risk"]},
    )
    return updated


async def decide_waiver(evaluation_id, waiver_id, payload, user):
    policy = QUALITY_POLICY
    codes = policy["error_codes"]
    value = await get_evaluation(
        evaluation_id, user, policy["permissions"]["waiver_approve"]
    )
    waiver = next(
        (item for item in value.get("waivers", []) if item["waiver_id"] == waiver_id), None
    )
    if not waiver:
        raise HTTPException(status_code=404, detail={"code": codes["waiver_not_found"]})
    if waiver["status"] != policy["pending_status"]:
        raise HTTPException(
            status_code=409, detail={"code": codes["waiver_already_decided"]}
        )
    waivers = [
        {
            **item,
            "status": policy["approved_status"]
            if payload.decision == policy["approve_decision"]
            else policy["rejected_status"],
            "approved_by": user.id,
            "approved_at": now(),
            "decision_note": payload.note,
        }
        if item["waiver_id"] == waiver_id
        else item
        for item in value["waivers"]
    ]
    updated = await quality_repository.update_evaluation(
        {
            "_id": evaluation_id,
            "revision": payload.expected_revision,
            "waivers.waiver_id": waiver_id,
        },
        {"$set": {"waivers": waivers, "updated_at": now()}, "$inc": {"revision": 1}},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["waiver_decided"],
        policy["entity_type"],
        evaluation_id,
        value["project_id"],
        {"waiver_id": waiver_id, "decision": payload.decision},
    )
    return updated


async def approve_evaluation(evaluation_id, payload, user):
    policy = QUALITY_POLICY
    codes = policy["error_codes"]
    value = await get_evaluation(evaluation_id, user, policy["permissions"]["approve"])
    if value["status"] != policy["review_status"]:
        raise HTTPException(status_code=409, detail={"code": codes["not_in_review"]})
    if not any(
        item.get("decision") == policy["endorse_decision"]
        for item in value.get("reviewed_by", [])
    ):
        raise HTTPException(
            status_code=409, detail={"code": codes["endorsement_required"]}
        )
    if any(
        item.get("status") == policy["pending_status"] for item in value.get("waivers", [])
    ):
        raise HTTPException(status_code=409, detail={"code": codes["pending_waiver"]})
    recommendation = value.get("system_recommendation", value.get("recommendation"))
    if (
        value.get("quality_gate_status") == policy["failed_gate_status"]
        and recommendation in policy["go_recommendations"]
        and not any(
            item.get("status") == policy["approved_status"]
            for item in value.get("waivers", [])
        )
    ):
        raise HTTPException(
            status_code=409, detail={"code": codes["failed_gate_waiver_required"]}
        )
    human_decision = await quality_repository.find_latest_decision(
        value["snapshot_id"], value["project_id"]
    )
    timestamp = now()
    updated = await quality_repository.update_evaluation(
        {
            "_id": evaluation_id,
            "revision": payload.expected_revision,
            "status": policy["review_status"],
        },
        {
            "$set": {
                "status": policy["approved_status"],
                "approved_by": user.id,
                "approved_at": timestamp,
                "approval_note": payload.note,
                "human_decision": human_decision,
                "quality_decision_id": human_decision.get("_id") if human_decision else None,
                "updated_at": timestamp,
            },
            "$inc": {"revision": 1},
        },
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["approved"],
        policy["entity_type"],
        evaluation_id,
        value["project_id"],
        {
            "recommendation": recommendation,
            "quality_decision_id": human_decision.get("_id") if human_decision else None,
        },
    )
    return updated


class QualityEvaluationService:
    @staticmethod
    async def list(project_id, release_id, user):
        return await list_evaluations(project_id, release_id, user)

    @staticmethod
    async def create(project_id, payload, user):
        return await create_evaluation(project_id, payload, user)

    @staticmethod
    async def get(evaluation_id, user):
        return await get_evaluation(evaluation_id, user)

    @staticmethod
    async def update(evaluation_id, payload, user):
        return await update_evaluation(evaluation_id, payload, user)

    @staticmethod
    async def submit(evaluation_id, payload, user):
        return await submit_evaluation(evaluation_id, payload, user)

    @staticmethod
    async def review(evaluation_id, payload, user):
        return await review_evaluation(evaluation_id, payload, user)

    @staticmethod
    async def add_waiver(evaluation_id, payload, user):
        return await add_waiver(evaluation_id, payload, user)

    @staticmethod
    async def decide_waiver(evaluation_id, waiver_id, payload, user):
        return await decide_waiver(evaluation_id, waiver_id, payload, user)

    @staticmethod
    async def approve(evaluation_id, payload, user):
        return await approve_evaluation(evaluation_id, payload, user)
