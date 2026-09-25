import math

from fastapi import HTTPException
from pymongo.errors import DuplicateKeyError

from src.core.common import audit, get_project, new_id, now
from src.repositories.statistical_quality import statistical_quality_repository
from src.services.domain_policy import domain_policy


def round_measurement(value):
    return round(value, domain_policy("process_control")["measurement_precision"])

def control_statistics(values):
    policy = domain_policy("process_control")
    if len(values) < policy["minimum_baseline_points"]:
        raise ValueError(policy["baseline_insufficient_code"])
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


async def get_statistical_analysis(analysis_id, user, permission=None):
    policy = domain_policy("process_control")
    value = await statistical_quality_repository.find_analysis(analysis_id)
    if not value:
        raise HTTPException(status_code=404, detail={"code": policy["entity_not_found_code"]})
    await get_project(value["project_id"], user, permission or policy["read_permission"])
    return value


async def list_statistical_analyses(project_id, user):
    policy = domain_policy("process_control")
    await get_project(project_id, user, policy["read_permission"])
    items = await statistical_quality_repository.list_analyses(
        {"project_id": project_id}, policy["analysis_limit"]
    )
    return {"items": items, "total": len(items)}


async def create_statistical_baseline(project_id, payload, user):
    policy = domain_policy("process_control")
    await get_project(project_id, user, policy["manage_permission"])
    if payload.idempotency_key:
        existing = await statistical_quality_repository.find_by_idempotency(
            project_id, payload.idempotency_key
        )
        if existing:
            if existing.get("measurement_definition_id") != payload.measurement_definition_id:
                raise HTTPException(
                    status_code=409, detail={"code": policy["idempotency_reused_code"]}
                )
            return existing
    definition = await statistical_quality_repository.find_definition(
        payload.measurement_definition_id, project_id
    )
    snapshots = await statistical_quality_repository.list_snapshots(
        project_id,
        payload.measurement_definition_id,
        payload.measurement_snapshot_refs,
        policy["snapshot_limit"],
    )
    if not definition or len(snapshots) != len(payload.measurement_snapshot_refs):
        raise HTTPException(
            status_code=422, detail={"code": policy["source_not_in_project_code"]}
        )
    if any(
        not isinstance(item.get("value"), (int, float)) or isinstance(item.get("value"), bool)
        for item in snapshots
    ):
        raise HTTPException(
            status_code=422, detail={"code": policy["value_not_numeric_code"]}
        )
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
        "_id": new_id(policy["analysis_id_prefix"]),
        "project_id": project_id,
        **payload.model_dump(),
        "measurement_key": definition.get("key"),
        "unit": definition.get("unit"),
        "points": points,
        "center_line": center,
        "lower_control_limit": lower,
        "upper_control_limit": upper,
        "outlier_snapshot_refs": outliers,
        "process_status": policy["unstable_status"] if outliers else policy["stable_status"],
        "alerts": [
            {"code": policy["instability_alert_code"], "snapshot_id": reference}
            for reference in outliers
        ],
        "calculation": policy["calculation_type"],
        "special_causes": [],
        "revision": policy["initial_revision"],
        "created_by": user.id,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    try:
        await statistical_quality_repository.insert_analysis(result)
    except DuplicateKeyError:
        if payload.idempotency_key:
            return await statistical_quality_repository.find_by_idempotency(
                project_id, payload.idempotency_key
            )
        raise
    await audit(
        user.id,
        policy["baseline_event"],
        policy["entity"],
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


async def annotate_special_cause(analysis_id, payload, user):
    policy = domain_policy("process_control")
    value = await get_statistical_analysis(analysis_id, user, policy["annotate_permission"])
    if payload.measurement_snapshot_id not in {item["snapshot_id"] for item in value["points"]}:
        raise HTTPException(
            status_code=422, detail={"code": policy["point_not_in_window_code"]}
        )
    timestamp = now()
    cause = {
        "annotation_id": new_id(policy["annotation_id_prefix"]),
        "measurement_snapshot_id": payload.measurement_snapshot_id,
        "cause": payload.cause,
        "evidence_refs": payload.evidence_refs,
        "created_by": user.id,
        "created_at": timestamp,
    }
    updated = await statistical_quality_repository.annotate(
        analysis_id, payload.expected_revision, cause, timestamp
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": policy["revision_conflict_code"]})
    await audit(
        user.id,
        policy["annotation_event"],
        policy["entity"],
        analysis_id,
        value["project_id"],
        {"snapshot_id": payload.measurement_snapshot_id, "evidence_refs": payload.evidence_refs},
    )
    return updated


async def compare_statistical_analyses(project_id, payload, user):
    policy = domain_policy("process_control")
    await get_project(project_id, user, policy["read_permission"])
    rows = await statistical_quality_repository.list_analyses_by_ids(
        project_id,
        [payload.before_analysis_id, payload.after_analysis_id],
        policy["comparison_limit"],
    )
    by_id = {item["_id"]: item for item in rows}
    if len(by_id) != 2:
        raise HTTPException(
            status_code=422, detail={"code": policy["comparison_source_code"]}
        )
    before = by_id[payload.before_analysis_id]
    after = by_id[payload.after_analysis_id]
    if before.get("measurement_definition_id") != after.get("measurement_definition_id"):
        raise HTTPException(
            status_code=422, detail={"code": policy["definition_mismatch_code"]}
        )
    proposal = None
    if payload.process_improvement_id:
        proposal = await statistical_quality_repository.find_improvement(
            payload.process_improvement_id, project_id
        )
        if not proposal:
            raise HTTPException(
                status_code=422, detail={"code": policy["improvement_not_in_project_code"]}
            )
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
        "calculation": policy["calculation_type"],
    }
