from fastapi import HTTPException

from src.core.common import audit, new_id, now
from src.repositories.test_completion import update_completion
from src.services.test_completion_query import get_completion_for_user, validate_people
from src.services.domain_policy import domain_policy


COMPLETION_POLICY = domain_policy("completion")


async def add_completion_residual_risk(report_id, payload, user):
    policy = COMPLETION_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    report = await get_completion_for_user(
        report_id, user, policy["permissions"]["risk_manage"]
    )
    if report["status"] != statuses["draft"]:
        raise HTTPException(status_code=409, detail={"code": codes["immutable"]})
    risk = payload.risk.model_dump()
    if risk["treatment"] != statuses["pending"]:
        raise HTTPException(
            status_code=422, detail={"code": codes["risk_decision_endpoint_required"]}
        )
    if any(item.get("risk_id") == risk["risk_id"] for item in report.get("residual_risks", [])):
        raise HTTPException(status_code=409, detail={"code": codes["risk_duplicate"]})
    await validate_people(report["project_id"], [risk["owner_id"]])
    updated = await update_completion(
        report_id,
        report["project_id"],
        payload.expected_revision,
        {statuses["draft"]},
        {"residual_risks": [*report.get("residual_risks", []), risk], "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["risk_added"],
        policy["entity_type"],
        report_id,
        report["project_id"],
        {"risk_id": risk["risk_id"]},
    )
    return updated


async def add_completion_lesson(report_id, payload, user):
    policy = COMPLETION_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    report = await get_completion_for_user(
        report_id, user, policy["permissions"]["lesson_create"]
    )
    if report["status"] != statuses["draft"]:
        raise HTTPException(status_code=409, detail={"code": codes["immutable"]})
    lesson = {
        **payload.lesson.model_dump(),
        "lesson_id": payload.lesson.lesson_id
        or new_id(policy["id_prefixes"]["lesson"]),
    }
    await validate_people(report["project_id"], [lesson.get("owner_id")])
    updated = await update_completion(
        report_id,
        report["project_id"],
        payload.expected_revision,
        {statuses["draft"]},
        {"lessons_learned": [*report.get("lessons_learned", []), lesson], "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["lesson_added"],
        policy["entity_type"],
        report_id,
        report["project_id"],
        {"lesson_id": lesson["lesson_id"], "category": lesson["category"]},
    )
    return updated


async def manage_completion_handover(report_id, payload, user):
    policy = COMPLETION_POLICY
    statuses = policy["statuses"]
    codes = policy["error_codes"]
    report = await get_completion_for_user(
        report_id, user, policy["permissions"]["handover_manage"]
    )
    if report["status"] != statuses["draft"]:
        raise HTTPException(status_code=409, detail={"code": codes["immutable"]})
    item = payload.item.model_dump()
    identity = (item["artifact_type"], item["artifact_id"], item.get("artifact_version_id"))
    handover = [
        value
        for value in report.get("testware_handover", [])
        if (value.get("artifact_type"), value.get("artifact_id"), value.get("artifact_version_id"))
        != identity
    ]
    handover.append(item)
    updated = await update_completion(
        report_id,
        report["project_id"],
        payload.expected_revision,
        {statuses["draft"]},
        {"testware_handover": handover, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": codes["revision_conflict"]})
    await audit(
        user.id,
        policy["events"]["handover_managed"],
        policy["entity_type"],
        report_id,
        report["project_id"],
        {
            "artifact_type": item["artifact_type"],
            "artifact_id": item["artifact_id"],
            "status": item["status"],
        },
    )
    return updated
