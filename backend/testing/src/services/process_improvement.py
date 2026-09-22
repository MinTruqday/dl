import math

from fastapi import HTTPException
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.services.domain_policy import domain_policy


def round_measurement(value):
    return round(value, domain_policy("process_control")["measurement_precision"])


async def require_member(db, project_id, user_id, code):
    member = await db.project_members.find_one(
        {"project_id": project_id, "user_id": user_id, "status": "ACTIVE"}
    )
    if not member:
        raise HTTPException(status_code=422, detail={"code": code})


async def get_proposal(db, proposal_id, user, permission="processimprovement.read"):
    value = await db.process_improvement_proposals.find_one({"_id": proposal_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, permission)
    return value


async def list_proposals(db, project_id, user):
    await get_project(project_id, user, "processimprovement.read")
    items = (
        await db.process_improvement_proposals.find({"project_id": project_id})
        .sort("updated_at", -1)
        .to_list(1000)
    )
    return {"items": items, "total": len(items)}


async def create_proposal(db, project_id, payload, user):
    await get_project(project_id, user, "processimprovement.create")
    await require_member(db, project_id, payload.owner_id, "IMPROVEMENT_OWNER_NOT_PROJECT_MEMBER")
    if payload.idempotency_key:
        existing = await db.process_improvement_proposals.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            if existing.get("observed_problem") != payload.observed_problem:
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    timestamp = now()
    value = {
        "_id": new_id("PIM"),
        "project_id": project_id,
        **payload.model_dump(),
        "lesson_refs": [],
        "causal_analysis_refs": [],
        "baseline_metrics": [],
        "result_metrics": [],
        "decision": None,
        "status": "PROPOSED",
        "history": [],
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await db.process_improvement_proposals.insert_one(value)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.process_improvement_proposals.find_one(
                {"project_id": project_id, "idempotency_key": payload.idempotency_key}
            )
        raise
    await audit(
        user.id,
        "process_improvement_created",
        "ProcessImprovementProposal",
        value["_id"],
        project_id,
        {"source": value["source"], "owner_id": value["owner_id"]},
    )
    return value


async def update_proposal(db, proposal_id, payload, user):
    value = await get_proposal(db, proposal_id, user, "processimprovement.update")
    if value["status"] != "PROPOSED":
        raise HTTPException(status_code=409, detail={"code": "IMPROVEMENT_PROPOSAL_IMMUTABLE"})
    changes = payload.model_dump(exclude_unset=True)
    changes.pop("expected_revision", None)
    if "owner_id" in changes:
        await require_member(
            db, value["project_id"], changes["owner_id"], "IMPROVEMENT_OWNER_NOT_PROJECT_MEMBER"
        )
    changes["updated_at"] = now()
    updated = await db.process_improvement_proposals.find_one_and_update(
        {"_id": proposal_id, "revision": payload.expected_revision, "status": "PROPOSED"},
        {"$set": changes, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "process_improvement_updated",
        "ProcessImprovementProposal",
        proposal_id,
        value["project_id"],
        {"fields": sorted(changes)},
    )
    return updated


async def link_sources(db, proposal_id, payload, user):
    value = await get_proposal(db, proposal_id, user, "processimprovement.update")
    if value["status"] != "PROPOSED":
        raise HTTPException(status_code=409, detail={"code": "IMPROVEMENT_PROPOSAL_IMMUTABLE"})
    causal = await db.causal_analyses.find(
        {"_id": {"$in": payload.causal_analysis_refs}, "project_id": value["project_id"]}
    ).to_list(1000)
    if len(causal) != len(set(payload.causal_analysis_refs)):
        raise HTTPException(status_code=422, detail={"code": "RCA_NOT_IN_PROJECT"})
    reports = await db.test_completion_reports.find(
        {
            "project_id": value["project_id"],
            "lessons_learned.lesson_id": {"$in": payload.lesson_refs},
        },
        {"lessons_learned": 1},
    ).to_list(1000)
    known_lessons = {
        item.get("lesson_id")
        for report in reports
        for item in report.get("lessons_learned", [])
        if item.get("lesson_id")
    }
    if set(payload.lesson_refs) - known_lessons:
        raise HTTPException(status_code=422, detail={"code": "LESSON_NOT_IN_PROJECT"})
    updated = await db.process_improvement_proposals.find_one_and_update(
        {"_id": proposal_id, "revision": payload.expected_revision, "status": "PROPOSED"},
        {
            "$set": {
                "lesson_refs": sorted(set(payload.lesson_refs)),
                "causal_analysis_refs": sorted(set(payload.causal_analysis_refs)),
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "process_improvement_sources_linked",
        "ProcessImprovementProposal",
        proposal_id,
        value["project_id"],
        {"lesson_refs": payload.lesson_refs, "causal_analysis_refs": payload.causal_analysis_refs},
    )
    return updated


async def metric_snapshots(db, project_id, references):
    items = await db.measurement_snapshots.find(
        {"_id": {"$in": references}, "project_id": project_id}
    ).to_list(1000)
    if len(items) != len(set(references)):
        raise HTTPException(status_code=422, detail={"code": "MEASUREMENT_NOT_IN_PROJECT"})
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


async def transition_proposal(db, proposal_id, payload, user, target, permission, event):
    value = await get_proposal(db, proposal_id, user, permission)
    allowed = {
        ("PROPOSED", "APPROVED_EXPERIMENT"),
        ("APPROVED_EXPERIMENT", "RUNNING"),
        ("EVALUATED", "ADOPTED"),
        ("EVALUATED", "REJECTED"),
    }
    if (value["status"], target) not in allowed:
        raise HTTPException(status_code=409, detail={"code": "INVALID_IMPROVEMENT_TRANSITION"})
    if target == "RUNNING" and not value.get("baseline_metrics"):
        raise HTTPException(status_code=409, detail={"code": "IMPROVEMENT_BASELINE_REQUIRED"})
    timestamp = now()
    entry = {
        "from": value["status"],
        "to": target,
        "actor_id": user.id,
        "note": payload.note,
        "at": timestamp,
    }
    changes = {"status": target, "updated_at": timestamp}
    if target in {"ADOPTED", "REJECTED"}:
        expected = "ADOPT" if target == "ADOPTED" else "REJECT"
        if value.get("decision") != expected:
            raise HTTPException(status_code=409, detail={"code": "IMPROVEMENT_DECISION_MISMATCH"})
        changes["decided_by"] = user.id
        changes["decided_at"] = timestamp
    updated = await db.process_improvement_proposals.find_one_and_update(
        {"_id": proposal_id, "revision": payload.expected_revision, "status": value["status"]},
        {"$set": changes, "$push": {"history": entry}, "$inc": {"revision": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id, event, "ProcessImprovementProposal", proposal_id, value["project_id"], entry
    )
    return updated


async def record_baseline(db, proposal_id, payload, user):
    value = await get_proposal(db, proposal_id, user, "processimprovement.measure")
    if value["status"] != "APPROVED_EXPERIMENT":
        raise HTTPException(status_code=409, detail={"code": "IMPROVEMENT_NOT_APPROVED"})
    metrics = await metric_snapshots(db, value["project_id"], payload.measurement_snapshot_refs)
    updated = await db.process_improvement_proposals.find_one_and_update(
        {
            "_id": proposal_id,
            "revision": payload.expected_revision,
            "status": "APPROVED_EXPERIMENT",
        },
        {
            "$set": {
                "baseline_metrics": metrics,
                "baseline_note": payload.note,
                "updated_at": now(),
            },
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "process_improvement_baseline_recorded",
        "ProcessImprovementProposal",
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


async def evaluate_proposal(db, proposal_id, payload, user):
    value = await get_proposal(db, proposal_id, user, "processimprovement.evaluate")
    if value["status"] != "RUNNING":
        raise HTTPException(status_code=409, detail={"code": "IMPROVEMENT_NOT_RUNNING"})
    metrics = await metric_snapshots(db, value["project_id"], payload.measurement_snapshot_refs)
    comparison = compare_metric_results(value.get("baseline_metrics", []), metrics)
    timestamp = now()
    history = {
        "from": "RUNNING",
        "to": "EVALUATED",
        "actor_id": user.id,
        "note": payload.note,
        "at": timestamp,
    }
    updated = await db.process_improvement_proposals.find_one_and_update(
        {"_id": proposal_id, "revision": payload.expected_revision, "status": "RUNNING"},
        {
            "$set": {
                "result_metrics": metrics,
                "result_comparison": comparison,
                "decision": payload.decision,
                "conclusion": payload.conclusion,
                "status": "EVALUATED",
                "evaluated_by": user.id,
                "evaluated_at": timestamp,
                "updated_at": timestamp,
            },
            "$push": {"history": history},
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "process_improvement_evaluated",
        "ProcessImprovementProposal",
        proposal_id,
        value["project_id"],
        {
            "decision": payload.decision,
            "snapshot_refs": payload.measurement_snapshot_refs,
            "comparison": comparison,
        },
    )
    return updated


def control_statistics(values):
    policy = domain_policy("process_control")
    if len(values) < policy["minimum_baseline_points"]:
        raise ValueError("STATISTICAL_BASELINE_INSUFFICIENT")
    center = sum(values) / len(values)
    variance = sum((value - center) ** 2 for value in values) / len(values)
    deviation = math.sqrt(variance)
    return (
        round_measurement(center),
        round_measurement(
            max(0, center - policy["standard_deviation_multiplier"] * deviation)
        ),
        round_measurement(center + policy["standard_deviation_multiplier"] * deviation),
    )


async def get_statistical_analysis(db, analysis_id, user, permission="statisticalquality.read"):
    value = await db.process_control_baselines.find_one({"_id": analysis_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    await get_project(value["project_id"], user, permission)
    return value


async def list_statistical_analyses(db, project_id, user):
    await get_project(project_id, user, "statisticalquality.read")
    items = (
        await db.process_control_baselines.find({"project_id": project_id})
        .sort("created_at", -1)
        .to_list(1000)
    )
    return {"items": items, "total": len(items)}


async def create_statistical_baseline(db, project_id, payload, user):
    await get_project(project_id, user, "statisticalquality.manage")
    if payload.idempotency_key:
        existing = await db.process_control_baselines.find_one(
            {"project_id": project_id, "idempotency_key": payload.idempotency_key}
        )
        if existing:
            if existing.get("measurement_definition_id") != payload.measurement_definition_id:
                raise HTTPException(status_code=409, detail={"code": "IDEMPOTENCY_KEY_REUSED"})
            return existing
    definition = await db.measurement_definitions.find_one(
        {"_id": payload.measurement_definition_id, "project_id": project_id}
    )
    snapshots = (
        await db.measurement_snapshots.find(
            {
                "_id": {"$in": payload.measurement_snapshot_refs},
                "project_id": project_id,
                "measurement_definition_id": payload.measurement_definition_id,
            }
        )
        .sort("measured_at", 1)
        .to_list(1000)
    )
    if not definition or len(snapshots) != len(payload.measurement_snapshot_refs):
        raise HTTPException(status_code=422, detail={"code": "STATISTICAL_SOURCE_NOT_IN_PROJECT"})
    if any(
        not isinstance(item.get("value"), (int, float)) or isinstance(item.get("value"), bool)
        for item in snapshots
    ):
        raise HTTPException(status_code=422, detail={"code": "STATISTICAL_VALUE_NOT_NUMERIC"})
    values = [float(item["value"]) for item in snapshots]
    center, lower, upper = control_statistics(values)
    points = [
        {
            "snapshot_id": item["_id"],
            "value": float(item["value"]),
            "measured_at": item.get("measured_at"),
            "outlier": float(item["value"]) < lower or float(item["value"]) > upper,
        }
        for item in snapshots
    ]
    outliers = [item["snapshot_id"] for item in points if item["outlier"]]
    timestamp = now()
    result = {
        "_id": new_id("SQC"),
        "project_id": project_id,
        **payload.model_dump(),
        "measurement_key": definition.get("key"),
        "unit": definition.get("unit"),
        "points": points,
        "center_line": center,
        "lower_control_limit": lower,
        "upper_control_limit": upper,
        "outlier_snapshot_refs": outliers,
        "process_status": "UNSTABLE" if outliers else "STABLE",
        "alerts": [
            {"code": "PROCESS_INSTABILITY_DETECTED", "snapshot_id": reference}
            for reference in outliers
        ],
        "calculation": "DETERMINISTIC",
        "special_causes": [],
        "revision": 1,
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await db.process_control_baselines.insert_one(result)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await db.process_control_baselines.find_one(
                {"project_id": project_id, "idempotency_key": payload.idempotency_key}
            )
        raise
    await audit(
        user.id,
        "statistical_baseline_calculated",
        "StatisticalQualityAnalysis",
        result["_id"],
        project_id,
        {
            "center_line": center,
            "lower_control_limit": lower,
            "upper_control_limit": upper,
            "outlier_count": len(outliers),
        },
    )
    return result


async def annotate_special_cause(db, analysis_id, payload, user):
    value = await get_statistical_analysis(db, analysis_id, user, "statisticalquality.annotate")
    if payload.measurement_snapshot_id not in {item["snapshot_id"] for item in value["points"]}:
        raise HTTPException(status_code=422, detail={"code": "STATISTICAL_POINT_NOT_IN_WINDOW"})
    timestamp = now()
    cause = {
        "annotation_id": new_id("SQCANN"),
        "measurement_snapshot_id": payload.measurement_snapshot_id,
        "cause": payload.cause,
        "evidence_refs": payload.evidence_refs,
        "created_by": user.id,
        "created_at": timestamp,
    }
    updated = await db.process_control_baselines.find_one_and_update(
        {"_id": analysis_id, "revision": payload.expected_revision},
        {
            "$push": {"special_causes": cause},
            "$set": {"updated_at": timestamp},
            "$inc": {"revision": 1},
        },
        return_document=ReturnDocument.AFTER,
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": "REVISION_CONFLICT"})
    await audit(
        user.id,
        "statistical_special_cause_annotated",
        "StatisticalQualityAnalysis",
        analysis_id,
        value["project_id"],
        {"snapshot_id": payload.measurement_snapshot_id, "evidence_refs": payload.evidence_refs},
    )
    return updated


async def compare_statistical_analyses(db, project_id, payload, user):
    await get_project(project_id, user, "statisticalquality.read")
    rows = await db.process_control_baselines.find(
        {
            "_id": {"$in": [payload.before_analysis_id, payload.after_analysis_id]},
            "project_id": project_id,
        }
    ).to_list(2)
    by_id = {item["_id"]: item for item in rows}
    if len(by_id) != 2:
        raise HTTPException(
            status_code=422, detail={"code": "STATISTICAL_COMPARISON_SOURCE_NOT_IN_PROJECT"}
        )
    before = by_id[payload.before_analysis_id]
    after = by_id[payload.after_analysis_id]
    if before.get("measurement_definition_id") != after.get("measurement_definition_id"):
        raise HTTPException(status_code=422, detail={"code": "STATISTICAL_DEFINITION_MISMATCH"})
    proposal = None
    if payload.process_improvement_id:
        proposal = await db.process_improvement_proposals.find_one(
            {"_id": payload.process_improvement_id, "project_id": project_id}
        )
        if not proposal:
            raise HTTPException(status_code=422, detail={"code": "IMPROVEMENT_NOT_IN_PROJECT"})
    return {
        "project_id": project_id,
        "before_analysis_id": before["_id"],
        "after_analysis_id": after["_id"],
        "process_improvement_id": proposal.get("_id") if proposal else None,
        "center_line_delta": round_measurement(
            after["center_line"] - before["center_line"]
        ),
        "control_width_before": round_measurement(
            before["upper_control_limit"] - before["lower_control_limit"]
        ),
        "control_width_after": round_measurement(
            after["upper_control_limit"] - after["lower_control_limit"]
        ),
        "outlier_count_before": len(before.get("outlier_snapshot_refs", [])),
        "outlier_count_after": len(after.get("outlier_snapshot_refs", [])),
        "calculation": "DETERMINISTIC",
    }
