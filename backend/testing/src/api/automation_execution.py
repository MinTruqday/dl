from fastapi import APIRouter, Depends, Header

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import (
    AutomationExecutionAction,
    AutomationExecutionCreate,
    AutomationExecutionResultInput,
)
from src.services.automation_execution import AutomationExecutionService

router = APIRouter(prefix="/kiem-thu", tags=["Thực thi tự động"])
internal_router = APIRouter(
    prefix="/noi-bo/kiem-thu/thuc-thi-tu-dong",
    tags=["Thực thi tự động nội bộ"],
)


@router.get("/du-an/{project_id}/thuc-thi-tu-dong")
async def list_automation_executions(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await AutomationExecutionService.list(project_id, user))


@router.get("/thuc-thi-tu-dong/{execution_id}")
async def get_automation_execution(
    execution_id: str, user: CurrentUser = Depends(get_current_user)
):
    value = await AutomationExecutionService.get(execution_id, user)
    return envelope(value, revision=value["revision"])


@router.post("/du-an/{project_id}/thuc-thi-tu-dong", status_code=201)
async def create_automation_execution(
    project_id: str,
    payload: AutomationExecutionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await AutomationExecutionService.create(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/thuc-thi-tu-dong/{execution_id}/bat-dau", status_code=202)
async def start_automation_execution(
    execution_id: str,
    payload: AutomationExecutionAction,
    user: CurrentUser = Depends(get_current_user),
):
    value, operation_id = await AutomationExecutionService.start(execution_id, payload, user)
    return envelope(value, operation_id=operation_id)


@router.post("/thuc-thi-tu-dong/{execution_id}/huy")
async def cancel_automation_execution(
    execution_id: str,
    payload: AutomationExecutionAction,
    user: CurrentUser = Depends(get_current_user),
):
    value = await AutomationExecutionService.cancel(execution_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/thuc-thi-tu-dong/{execution_id}/bang-chung")
async def get_automation_evidence(
    execution_id: str, user: CurrentUser = Depends(get_current_user)
):
    value = await AutomationExecutionService.get(execution_id, user, evidence=True)
    return envelope(value, revision=value["revision"])


@internal_router.post("/ket-qua", include_in_schema=False)
async def ingest_automation_result(
    payload: AutomationExecutionResultInput,
    x_internal_token: str = Header(default=""),
):
    value = await AutomationExecutionService.ingest_result(payload, x_internal_token)
    return envelope(value, revision=value["revision"])
