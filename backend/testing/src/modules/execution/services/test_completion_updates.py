from fastapi import HTTPException

from src.core.common import audit, new_id, now
from src.repositories.test_completion import update_completion
from src.modules.execution.services.test_completion_query import get_completion_for_user, validate_people





async def add_completion_residual_risk(report_id, payload, user):
    
    
    
    report = await get_completion_for_user(
        report_id, user, 'testcompletion.risk.manage'
    )
    if report["status"] != 'DRAFT':
        raise HTTPException(status_code=409, detail={"code": 'COMPLETION_REPORT_IMMUTABLE'})
    risk = payload.risk.model_dump()
    if risk["treatment"] != 'PENDING':
        raise HTTPException(
            status_code=422, detail={"code": 'RESIDUAL_RISK_DECISION_ENDPOINT_REQUIRED'}
        )
    if any(item.get("risk_id") == risk["risk_id"] for item in report.get("residual_risks", [])):
        raise HTTPException(status_code=409, detail={"code": 'RESIDUAL_RISK_DUPLICATE'})
    await validate_people(report["project_id"], [risk["owner_id"]])
    updated = await update_completion(
        report_id,
        report["project_id"],
        payload.expected_revision,
        {'DRAFT'},
        {"residual_risks": [*report.get("residual_risks", []), risk], "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": 'COMPLETION_REPORT_REVISION_CONFLICT'})
    await audit(
        user.id,
        'test_completion_residual_risk_added',
        'TestCompletionReport',
        report_id,
        report["project_id"],
        {"risk_id": risk["risk_id"]},
    )
    return updated


async def add_completion_lesson(report_id, payload, user):
    
    
    
    report = await get_completion_for_user(
        report_id, user, 'testcompletion.lesson.create'
    )
    if report["status"] != 'DRAFT':
        raise HTTPException(status_code=409, detail={"code": 'COMPLETION_REPORT_IMMUTABLE'})
    lesson = {
        **payload.lesson.model_dump(),
        "lesson_id": payload.lesson.lesson_id
        or new_id('LESSON'),
    }
    await validate_people(report["project_id"], [lesson.get("owner_id")])
    updated = await update_completion(
        report_id,
        report["project_id"],
        payload.expected_revision,
        {'DRAFT'},
        {"lessons_learned": [*report.get("lessons_learned", []), lesson], "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": 'COMPLETION_REPORT_REVISION_CONFLICT'})
    await audit(
        user.id,
        'test_completion_lesson_added',
        'TestCompletionReport',
        report_id,
        report["project_id"],
        {"lesson_id": lesson["lesson_id"], "category": lesson["category"]},
    )
    return updated


async def manage_completion_handover(report_id, payload, user):
    
    
    
    report = await get_completion_for_user(
        report_id, user, 'testcompletion.handover.manage'
    )
    if report["status"] != 'DRAFT':
        raise HTTPException(status_code=409, detail={"code": 'COMPLETION_REPORT_IMMUTABLE'})
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
        {'DRAFT'},
        {"testware_handover": handover, "updated_at": now()},
    )
    if not updated:
        raise HTTPException(status_code=409, detail={"code": 'COMPLETION_REPORT_REVISION_CONFLICT'})
    await audit(
        user.id,
        'test_completion_handover_managed',
        'TestCompletionReport',
        report_id,
        report["project_id"],
        {
            "artifact_type": item["artifact_type"],
            "artifact_id": item["artifact_id"],
            "status": item["status"],
        },
    )
    return updated
