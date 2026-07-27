from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from src.core.dependency import CurrentUser, get_current_user

router = APIRouter(prefix="/ngat-qua-trinh")


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

        await supervisor_app.aupdate_state(config, {}, as_node=state.next[0])
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
