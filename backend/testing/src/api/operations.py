from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.services.operations import OperationsService

router = APIRouter(prefix="/kiem-thu", tags=["Vận hành kiểm thử"])


@router.get("/van-hanh")
async def operations(
    limit: int = Query(default=100, ge=1, le=500),
    audit_q: str = Query(default="", max_length=200),
    audit_event: str = Query(default="", max_length=120),
    audit_project_id: str = Query(default="", max_length=128),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(
        await OperationsService.overview(
            limit, audit_q, audit_event, audit_project_id, user
        )
    )


@router.post("/van-hanh/tac-vu/{job_id}/thu-lai", status_code=202)
async def retry_failed_job(job_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await OperationsService.retry_failed_job(job_id, user))
