from fastapi import APIRouter, Depends, Header

from src.core.common import envelope
from src.core.internal import require_internal_token
from src.services.job_execution import process_delegated_job

router = APIRouter(prefix="/kiem-thu/noi-bo/tac-vu", tags=["Tác vụ nội bộ kiểm thử"])


@router.post("/{event}")
async def process_job(
    event: str,
    body: dict,
    x_requester_id: str = Header(default=""),
    x_requester_email: str = Header(default=""),
    _: None = Depends(require_internal_token),
):
    return envelope(
        await process_delegated_job(event, body, x_requester_id, x_requester_email)
    )
