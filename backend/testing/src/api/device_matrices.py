from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import (
    DeviceMatrixArchive,
    DeviceMatrixAssignment,
    DeviceMatrixCreate,
    DeviceMatrixPatch,
)
from src.services.device_matrix import DeviceMatrixService

router = APIRouter(prefix="/kiem-thu", tags=["Ma trận thiết bị"])


@router.get("/du-an/{project_id}/ma-tran-thiet-bi", openapi_extra={"x-function-ids": ["DEVMTX-01"]})
async def list_device_matrices(
    project_id: str,
    include_archived: bool = Query(default=False),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await DeviceMatrixService.list(project_id, include_archived, user))


@router.get("/ma-tran-thiet-bi/{matrix_id}", openapi_extra={"x-function-ids": ["DEVMTX-01"]})
async def get_device_matrix(matrix_id: str, user: CurrentUser = Depends(get_current_user)):
    matrix = await DeviceMatrixService.get(matrix_id, user)
    return envelope(matrix, revision=matrix["revision"])


@router.post(
    "/du-an/{project_id}/ma-tran-thiet-bi",
    status_code=201,
    openapi_extra={"x-function-ids": ["DEVMTX-02"]},
)
async def create_device_matrix(
    project_id: str, payload: DeviceMatrixCreate, user: CurrentUser = Depends(get_current_user)
):
    matrix = await DeviceMatrixService.create(project_id, payload, user)
    return envelope(matrix, revision=1)


@router.patch("/ma-tran-thiet-bi/{matrix_id}", openapi_extra={"x-function-ids": ["DEVMTX-02"]})
async def update_device_matrix(
    matrix_id: str, payload: DeviceMatrixPatch, user: CurrentUser = Depends(get_current_user)
):
    updated = await DeviceMatrixService.update(matrix_id, payload, user)
    return envelope(updated, revision=updated["revision"])


@router.post(
    "/ma-tran-thiet-bi/{matrix_id}/luu-tru", openapi_extra={"x-function-ids": ["DEVMTX-02"]}
)
async def archive_device_matrix(
    matrix_id: str, payload: DeviceMatrixArchive, user: CurrentUser = Depends(get_current_user)
):
    updated = await DeviceMatrixService.archive(matrix_id, payload, user)
    return envelope(updated, revision=updated["revision"])


@router.post("/ma-tran-thiet-bi/{matrix_id}/gan", openapi_extra={"x-function-ids": ["DEVMTX-03"]})
async def assign_device_matrix(
    matrix_id: str, payload: DeviceMatrixAssignment, user: CurrentUser = Depends(get_current_user)
):
    updated = await DeviceMatrixService.assign(matrix_id, payload, user)
    return envelope(updated, revision=updated["revision"])
