from fastapi import APIRouter, Depends

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import (
    ConnectorConflictResolution,
    ConnectorSyncInput,
    ProjectConnectorCreate,
    ProjectConnectorPatch,
    ProjectConnectorUnbind,
)
from src.services.project_connector import ProjectConnectorService

router = APIRouter(prefix="/kiem-thu", tags=["Kết nối dự án"])


@router.get("/du-an/{project_id}/ket-noi")
async def list_project_connectors(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await ProjectConnectorService.list(project_id, user))


@router.post("/du-an/{project_id}/ket-noi", status_code=201)
async def bind_project_connector(
    project_id: str,
    payload: ProjectConnectorCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProjectConnectorService.bind(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.patch("/du-an/{project_id}/ket-noi/{connector_id}")
async def update_project_connector(
    project_id: str,
    connector_id: str,
    payload: ProjectConnectorPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProjectConnectorService.update(project_id, connector_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/du-an/{project_id}/ket-noi/{connector_id}/ngat")
async def unbind_project_connector(
    project_id: str,
    connector_id: str,
    payload: ProjectConnectorUnbind,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProjectConnectorService.unbind(project_id, connector_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/du-an/{project_id}/ket-noi/{connector_id}/dong-bo", status_code=202)
async def start_connector_sync(
    project_id: str,
    connector_id: str,
    payload: ConnectorSyncInput,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProjectConnectorService.start_sync(project_id, connector_id, payload, user)
    return envelope(value, operation_id=value["_id"])


@router.get("/du-an/{project_id}/ket-noi/nhat-ky")
async def list_connector_sync_log(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await ProjectConnectorService.list_sync_log(project_id, user))


@router.get("/du-an/{project_id}/ket-noi/xung-dot")
async def list_connector_conflicts(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await ProjectConnectorService.list_conflicts(project_id, user))


@router.post("/du-an/{project_id}/ket-noi/xung-dot/{conflict_id}/giai-quyet")
async def resolve_connector_conflict(
    project_id: str,
    conflict_id: str,
    payload: ConnectorConflictResolution,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProjectConnectorService.resolve_conflict(
        project_id, conflict_id, payload, user
    )
    return envelope(value, revision=value["revision"])
