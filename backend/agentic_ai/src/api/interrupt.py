import asyncio

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from src.core.dependency import CurrentUser, get_current_user
from src.schemas.intervention import InterventionFeedbackRequest
from src.utils.background import create_background_task

router = APIRouter(prefix="/ngat-qua-trinh")
_running_workflows: dict[str, asyncio.Task] = {}


@router.get("/phe-duyet/{session_id}")
async def pending_approvals(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return pending sensitive actions owned by the authenticated session user"""
    from dataclasses import asdict

    from src.loop.intervention import intervention

    requests = [
        request
        for request in await intervention.get_pending_by_session(session_id)
        if request.user_id == str(current_user.id)
    ]
    return {
        "status": "success",
        "data": [asdict(request) for request in requests],
    }


@router.post("/phe-duyet/phan-hoi/{intervention_id}")
async def resolve_approval(
    intervention_id: str,
    req: InterventionFeedbackRequest,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Resolve one pending sensitive action after verifying its authenticated owner"""
    from dataclasses import asdict

    from src.loop.intervention import intervention

    pending = await intervention.check_pending(intervention_id)
    if not pending or pending.user_id != str(current_user.id):
        raise HTTPException(
            status_code=404,
            detail={"code": "approval_not_found"},
        )
    resolved = await intervention.record_feedback(
        intervention_id=intervention_id,
        status=req.status,
        human_feedback=req.human_feedback,
        correction=req.correction,
    )
    if not resolved:
        raise HTTPException(
            status_code=409,
            detail={"code": "approval_resolution_failed"},
        )
    return {
        "status": "success",
        "data": asdict(resolved),
    }


async def _resume_from_checkpoint(thread_id: str, config: dict) -> None:
    from src.workflow.orchestration import supervisor_app

    try:
        async for _ in supervisor_app.astream(None, config=config):
            continue
    finally:
        _running_workflows.pop(thread_id, None)


@router.post("/tiep-tuc/{thread_id}")
async def resume_workflow(
    thread_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    <api_purpose>
    <purpose>Resumes a paused workflow from its last checkpoint after user confirmation.</purpose>
    <metis_behavior>Loads the checkpointed state via MemorySaver and resumes the graph stream from the interrupt point.</metis_behavior>
    </api_purpose>
    """
    from src.workflow.orchestration import supervisor_app

    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = await supervisor_app.aget_state(config)
        if not state or not state.next:
            raise HTTPException(status_code=404, detail={"code": "workflow_not_resumable"})
        if str(state.values.get("req_data", {}).get("user_id", "")) != str(current_user.id):
            raise HTTPException(status_code=404, detail={"code": "workflow_not_resumable"})

        running = _running_workflows.get(thread_id)
        if running and not running.done():
            raise HTTPException(
                status_code=409,
                detail={"code": "workflow_already_running"},
            )
        task = create_background_task(
            _resume_from_checkpoint(thread_id, config),
            f"workflow-resume-{thread_id}",
        )
        _running_workflows[thread_id] = task
        logger.info(f"Workflow resumed for thread {thread_id}")
        return {"message_code": "workflow_resumed"}
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Workflow resume failed for thread {thread_id}")
        raise HTTPException(status_code=500, detail={"code": "workflow_resume_failed"})


@router.post("/huy-bo/{thread_id}")
async def cancel_workflow(
    thread_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """
    <api_purpose>
    <purpose>Cancels a paused or running workflow and clears its checkpoint.</purpose>
    </api_purpose>
    """
    from src.workflow.orchestration import supervisor_app

    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = await supervisor_app.aget_state(config)
        if not state or str(state.values.get("req_data", {}).get("user_id", "")) != str(current_user.id):
            raise HTTPException(status_code=404, detail={"code": "workflow_not_cancellable"})
        running = _running_workflows.pop(thread_id, None)
        if running and not running.done():
            running.cancel()
        await supervisor_app.aupdate_state(
            config,
            {"error": "workflow_cancelled", "next_nodes": ["trimmer"]},
        )
        logger.info(f"Workflow cancelled for thread {thread_id}")
        return {"message_code": "workflow_cancelled"}
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Workflow cancel failed for thread {thread_id}")
        raise HTTPException(status_code=500, detail={"code": "workflow_cancellation_failed"})


@router.get("/trang-thai/{thread_id}")
async def workflow_status(
    thread_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Return ownership checked execution status for one checkpointed workflow"""
    from src.workflow.orchestration import supervisor_app

    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = await supervisor_app.aget_state(config)
        if not state or str(state.values.get("req_data", {}).get("user_id", "")) != str(current_user.id):
            raise HTTPException(
                status_code=404,
                detail={"code": "workflow_not_found"},
            )
        running = _running_workflows.get(thread_id)
        if running and not running.done():
            status = "running"
        elif state.values.get("error"):
            status = "failed"
        elif state.next:
            status = "paused"
        else:
            status = "completed"
        return {
            "thread_id": thread_id,
            "status": status,
            "next_nodes": list(state.next),
            "error": state.values.get("error", ""),
            "completed_tasks": state.values.get("completed_tasks", []),
        }
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Workflow status lookup failed for thread {thread_id}")
        raise HTTPException(
            status_code=500,
            detail={"code": "workflow_status_failed"},
        )
