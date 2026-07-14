from fastapi import APIRouter, HTTPException
from loguru import logger

router = APIRouter(prefix="/ngat-qua-trinh")


@router.post("/tiep-tuc/{thread_id}")
async def resume_workflow(thread_id: str):
    """
    <api_purpose>
    <purpose>Resumes a paused workflow from its last checkpoint after user confirmation.</purpose>
    <metis_behavior>Loads the checkpointed state via MemorySaver and resumes the graph stream from the interrupt point.</metis_behavior>
    </api_purpose>
    """
    from src.workflow.orchestration import supervisor_app

    config = {"configurable": {"thread_id": thread_id}}
    try:
        state = supervisor_app.get_state(config)
        if not state or not state.next:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tiến trình cần tiếp tục")

        await supervisor_app.aupdate_state(config, {}, as_node=state.next[0])
        logger.info(f"Workflow resumed for thread {thread_id}")
        return {"message": "Tiến trình đã được tiếp tục"}
    except HTTPException:
        raise
    except Exception:
        logger.exception(f"Workflow resume failed for thread {thread_id}")
        raise HTTPException(status_code=500, detail="Hệ thống không thể tiếp tục tiến trình")


@router.post("/huy-bo/{thread_id}")
async def cancel_workflow(thread_id: str):
    """
    <api_purpose>
    <purpose>Cancels a paused or running workflow and clears its checkpoint.</purpose>
    </api_purpose>
    """
    from src.workflow.orchestration import supervisor_app

    config = {"configurable": {"thread_id": thread_id}}
    try:
        await supervisor_app.aupdate_state(
            config,
            {"error": "Tiến trình đã bị hủy theo yêu cầu của người dùng", "next_nodes": ["trimmer"]},
        )
        logger.info(f"Workflow cancelled for thread {thread_id}")
        return {"message": "Tiến trình đã bị hủy"}
    except Exception:
        logger.exception(f"Workflow cancel failed for thread {thread_id}")
        raise HTTPException(status_code=500, detail="Hệ thống không thể hủy tiến trình")
