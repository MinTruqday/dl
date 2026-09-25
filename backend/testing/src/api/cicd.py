from fastapi import APIRouter, Depends, Header

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import (
    CiCdBindingCreate,
    CiCdBindingPatch,
    CiCdResultInput,
    CiCdRetryInput,
    CiCdTriggerInput,
)
from src.services.cicd import CiCdService

router = APIRouter(prefix="/kiem-thu", tags=["Tích hợp triển khai liên tục"])
internal_router = APIRouter(
    prefix="/noi-bo/kiem-thu/tich-hop-trien-khai-lien-tuc",
    tags=["Tích hợp triển khai liên tục nội bộ"],
)


@router.get("/du-an/{project_id}/tich-hop-trien-khai-lien-tuc")
async def list_cicd_state(project_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await CiCdService.list_state(project_id, user))


@router.post("/du-an/{project_id}/tich-hop-trien-khai-lien-tuc", status_code=201)
async def create_cicd_binding(
    project_id: str,
    payload: CiCdBindingCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await CiCdService.create_binding(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.patch("/du-an/{project_id}/tich-hop-trien-khai-lien-tuc/{binding_id}")
async def update_cicd_binding(
    project_id: str,
    binding_id: str,
    payload: CiCdBindingPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await CiCdService.update_binding(project_id, binding_id, payload, user)
    return envelope(value, revision=value["revision"])


@internal_router.post("/kich-hoat", include_in_schema=False, status_code=202)
async def trigger_cicd_run(
    payload: CiCdTriggerInput, x_internal_token: str = Header(default="")
):
    value = await CiCdService.trigger(payload, x_internal_token)
    return envelope(value, operation_id=value["_id"])


@internal_router.post("/ket-qua", include_in_schema=False)
async def ingest_cicd_result(
    payload: CiCdResultInput, x_internal_token: str = Header(default="")
):
    value = await CiCdService.ingest_result(payload, x_internal_token)
    return envelope(value, revision=value["revision"])


@router.post(
    "/du-an/{project_id}/tich-hop-trien-khai-lien-tuc/lan-chay/{run_id}/thu-lai",
    status_code=202,
)
async def retry_cicd_run(
    project_id: str,
    run_id: str,
    payload: CiCdRetryInput,
    user: CurrentUser = Depends(get_current_user),
):
    value = await CiCdService.retry(project_id, run_id, payload, user)
    return envelope(value, operation_id=value["_id"])
