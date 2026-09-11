from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.core.database import database
from src.domain.measurement import MeasurementDefinitionCreate, MeasurementDefinitionPatch, MeasurementSnapshotCreate, MeasurementTransition
from src.services.measurement_service import create_definition, create_snapshot, list_definitions, list_snapshots, transition_definition, update_definition


router = APIRouter(prefix="/kiem-thu", tags=["Đo lường kiểm thử"])


@router.get("/du-an/{project_id}/dinh-nghia-do-luong")
async def list_measurement_definitions(project_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await list_definitions(database.value, project_id, user))


@router.post("/du-an/{project_id}/dinh-nghia-do-luong", status_code=201)
async def create_measurement_definition(project_id: str, payload: MeasurementDefinitionCreate, user: CurrentUser = Depends(get_current_user)):
    value = await create_definition(database.value, project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.patch("/dinh-nghia-do-luong/{definition_id}")
async def patch_measurement_definition(definition_id: str, payload: MeasurementDefinitionPatch, user: CurrentUser = Depends(get_current_user)):
    value = await update_definition(database.value, definition_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/dinh-nghia-do-luong/{definition_id}/trang-thai")
async def transition_measurement_definition(definition_id: str, payload: MeasurementTransition, user: CurrentUser = Depends(get_current_user)):
    value = await transition_definition(database.value, definition_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/du-an/{project_id}/anh-do-luong")
async def list_measurement_snapshots(project_id: str, definition_id: str = Query(default=""), release_id: str = Query(default=""), user: CurrentUser = Depends(get_current_user)):
    return envelope(await list_snapshots(database.value, project_id, user, definition_id, release_id))


@router.post("/du-an/{project_id}/anh-do-luong", status_code=201)
async def create_measurement_snapshot(project_id: str, payload: MeasurementSnapshotCreate, user: CurrentUser = Depends(get_current_user)):
    return envelope(await create_snapshot(database.value, project_id, payload, user))


@router.get("/anh-do-luong/{snapshot_id}")
async def get_measurement_snapshot(snapshot_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await database.value.measurement_snapshots.find_one({"_id": snapshot_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    from src.core.common import get_project
    await get_project(value["project_id"], user, "measurement.read")
    return envelope(value)
