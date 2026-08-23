from fastapi import APIRouter, Depends, HTTPException

from src.core.dependency import CurrentUser, get_current_user
from src.schemas.intervention import InterventionFeedbackRequest

router = APIRouter(prefix="/ngat-qua-trinh")


@router.post("/{session_id}")
async def cancel_execution(
    session_id: str,
    current_user: CurrentUser = Depends(get_current_user),
):
    """Cancel one authenticated session and persist its cancelled workspace state"""
    from src.harness.orchestration import orchestration
    from src.services.history import HistoryService
    from src.services.workspace import workspace

    user_id = str(current_user.id)
    await HistoryService.get_session_detail(session_id, user_id)
    orchestration.cancel_session(session_id)
    await workspace.set_status(session_id, user_id, "cancelled")
    return {"status": "cancelled", "session_id": session_id}


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
        scope=req.scope,
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
