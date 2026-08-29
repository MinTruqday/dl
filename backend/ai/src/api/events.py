import asyncio
from typing import Literal

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from loguru import logger

from src.agents.loop.event import AgentEvent, CronSchedule, EventType, cron_scheduler, event_driven_loop

from src.schemas.events import CreateScheduleRequest, ManualTriggerRequest, WebhookPayload
from src.core.dependency import Role, require_role, verify_internal_token

router = APIRouter(prefix="/su-kien")


@router.post("/webhook", dependencies=[Depends(verify_internal_token)])
async def receive_webhook(body: WebhookPayload):
    """Validate and enqueue an internal agent event webhook"""
    try:
        event_type_str = body.event_type.lower()
        event_type_map = {
            "webhook": EventType.WEBHOOK,
            "document_uploaded": EventType.DOCUMENT_UPLOADED,
            "user_query": EventType.USER_QUERY,
            "system_heartbeat": EventType.SYSTEM_HEARTBEAT,
            "document_deleted": EventType.DOCUMENT_DELETED,
            "user_registered": EventType.USER_REGISTERED,
        }
        event_type = event_type_map[event_type_str]

        event = AgentEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            payload=body.payload,
            source=body.source,
        )

        try:
            await event_driven_loop.emit_event(event)
        except asyncio.QueueFull:
            raise HTTPException(status_code=503, detail={"code": "event_queue_full"})
        logger.info(f"Webhook received event_id={event.event_id}, type={event_type.value}")

        return {"status": "accepted", "event_id": event.event_id, "event_type": event_type.value}
    except HTTPException:
        raise
    except Exception:
        logger.exception("Webhook processing error")
        raise HTTPException(status_code=500, detail={"code": "webhook_processing_failed"})


@router.post("/webhook/tai-lieu-dang-tai", dependencies=[Depends(verify_internal_token)])
async def document_uploaded_webhook(
    document_id: str, user_id: str = "", superseded_document_id: str = ""
):
    """Enqueue a document upload event for indexing and verification"""
    event = AgentEvent(
        event_id=str(uuid.uuid4()),
        event_type=EventType.DOCUMENT_UPLOADED,
        payload={
            "document_id": document_id,
            "user_id": user_id,
            "superseded_document_id": superseded_document_id,
        },
        source="content_service",
    )
    try:
        await event_driven_loop.emit_event(event)
    except asyncio.QueueFull:
        raise HTTPException(status_code=503, detail={"code": "event_queue_full"})
    return {"status": "accepted", "event_id": event.event_id}


@router.get("/lich-trinh", dependencies=[Depends(require_role([Role.ADMIN]))])
async def list_schedules():
    """List every registered recurring agent schedule"""
    return {"schedules": cron_scheduler.list_schedules(), "total": len(cron_scheduler._schedules)}


@router.post("/lich-trinh", dependencies=[Depends(require_role([Role.ADMIN]))])
async def create_schedule(req: CreateScheduleRequest):
    """Create and activate an administrator managed recurring event"""
    event_type_map = {
        "system_heartbeat": EventType.SYSTEM_HEARTBEAT,
        "document_uploaded": EventType.DOCUMENT_UPLOADED,
        "user_query": EventType.USER_QUERY,
        "webhook": EventType.WEBHOOK,
    }
    event_type = event_type_map.get(req.event_type, EventType.SYSTEM_HEARTBEAT)

    schedule = CronSchedule(
        schedule_id=str(uuid.uuid4()),
        name=req.name,
        cron_expression=f"*/{req.interval_seconds // 60 or 1} * * * *",
        interval_seconds=req.interval_seconds,
        event_type=event_type,
        payload_template=req.payload_template,
        enabled=req.enabled,
    )
    cron_scheduler.register(schedule)

    if cron_scheduler._running and schedule.enabled:
        schedule._task = asyncio.create_task(
            cron_scheduler._run_schedule(schedule), name=f"cron:{schedule.name}"
        )

    return {
        "status": "created",
        "schedule_id": schedule.schedule_id,
        "name": schedule.name,
        "interval_seconds": schedule.interval_seconds,
    }


@router.delete("/lich-trinh/{schedule_id}", dependencies=[Depends(require_role([Role.ADMIN]))])
async def delete_schedule(schedule_id: str):
    """Delete one recurring agent schedule"""
    if schedule_id not in cron_scheduler._schedules:
        raise HTTPException(status_code=404, detail={"code": "schedule_not_found"})
    cron_scheduler.unregister(schedule_id)
    return {"status": "deleted", "schedule_id": schedule_id}


@router.patch(
    "/lich-trinh/{schedule_id}/trang-thai", dependencies=[Depends(require_role([Role.ADMIN]))]
)
async def toggle_schedule(schedule_id: str):
    """Enable or disable one recurring agent schedule"""
    schedule = cron_scheduler._schedules.get(schedule_id)
    if not schedule:
        raise HTTPException(status_code=404, detail={"code": "schedule_not_found"})
    cron_scheduler.set_enabled(schedule_id, not schedule.enabled)
    return {"schedule_id": schedule_id, "name": schedule.name, "enabled": schedule.enabled}


@router.get("/trang-thai", dependencies=[Depends(require_role([Role.ADMIN]))])
async def event_loop_status():
    """Return event queue and worker runtime statistics"""
    return event_driven_loop.get_stats()


@router.get("/lich-su", dependencies=[Depends(require_role([Role.ADMIN]))])
async def event_history(limit: int = Query(default=20, ge=1, le=200)):
    """Return recently processed agent events"""
    return {"events": event_driven_loop.get_recent_events(limit=limit)}


@router.get("/cap-nhat", dependencies=[Depends(require_role([Role.ADMIN]))])
async def system_updates(limit: int = Query(default=20, ge=1, le=200)):
    """Return recent state updates emitted by agent events"""
    updates = event_driven_loop.update_registry.get_recent(limit=limit)
    return {
        "updates": [
            {
                "update_id": u.update_id,
                "event_id": u.event_id,
                "update_type": u.update_type,
                "description": u.description,
                "applied_at": u.applied_at.isoformat(),
                "success": u.success,
            }
            for u in updates
        ],
        "stats": event_driven_loop.update_registry.get_stats(),
    }


@router.post("/kich-hoat/{event_type}", dependencies=[Depends(require_role([Role.ADMIN]))])
async def manual_trigger(
    event_type: Literal["heartbeat", "document_uploaded", "user_query"],
    req: ManualTriggerRequest = Body(default_factory=ManualTriggerRequest),
):
    """Trigger a supported agent event immediately"""
    event_type_map = {
        "heartbeat": EventType.SYSTEM_HEARTBEAT,
        "document_uploaded": EventType.DOCUMENT_UPLOADED,
        "user_query": EventType.USER_QUERY,
    }
    et = event_type_map[event_type]
    event = AgentEvent(
        event_id=str(uuid.uuid4()), event_type=et, payload=req.payload, source="manual_trigger"
    )
    result = await event_driven_loop.handle_event(event)
    return {"status": "triggered", "event_id": event.event_id, "result": result}


import uuid
