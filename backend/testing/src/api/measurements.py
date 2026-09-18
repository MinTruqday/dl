from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.core.database import database
from src.domain.measurement import (
    MeasurementDefinitionCreate,
    MeasurementDefinitionPatch,
    MeasurementSnapshotCreate,
    MeasurementTransition,
    MeasurementVersionCreate,
    MetricDashboardPin,
)
from src.services.measurement import (
    compare_measurement_releases,
    create_definition,
    create_snapshot,
    list_definitions,
    list_snapshots,
    measurement_alerts,
    measurement_trend,
    pin_metric,
    transition_definition,
    update_definition,
    validate_definition,
    version_definition,
)
from src.services.measurement_export import export_metric_csv

router = APIRouter(prefix="/kiem-thu", tags=["Đo lường kiểm thử"])


@router.get("/du-an/{project_id}/dinh-nghia-do-luong")
async def list_measurement_definitions(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await list_definitions(database.value, project_id, user))


@router.post("/du-an/{project_id}/dinh-nghia-do-luong", status_code=201)
async def create_measurement_definition(
    project_id: str,
    payload: MeasurementDefinitionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await create_definition(database.value, project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.patch("/dinh-nghia-do-luong/{definition_id}")
async def patch_measurement_definition(
    definition_id: str,
    payload: MeasurementDefinitionPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await update_definition(database.value, definition_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/dinh-nghia-do-luong/{definition_id}/tao-phien-ban", status_code=201)
async def version_measurement_definition(
    definition_id: str,
    payload: MeasurementVersionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await version_definition(database.value, definition_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/dinh-nghia-do-luong/{definition_id}/trang-thai")
async def transition_measurement_definition(
    definition_id: str,
    payload: MeasurementTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await transition_definition(database.value, definition_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/du-an/{project_id}/anh-do-luong")
async def list_measurement_snapshots(
    project_id: str,
    definition_id: str = Query(default=""),
    release_id: str = Query(default=""),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(
        await list_snapshots(database.value, project_id, user, definition_id, release_id)
    )


@router.post("/du-an/{project_id}/anh-do-luong", status_code=201)
async def create_measurement_snapshot(
    project_id: str,
    payload: MeasurementSnapshotCreate,
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await create_snapshot(database.value, project_id, payload, user))


@router.get("/anh-do-luong/{snapshot_id}")
async def get_measurement_snapshot(snapshot_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await database.value.measurement_snapshots.find_one({"_id": snapshot_id})
    if not value:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    from src.core.common import get_project

    await get_project(value["project_id"], user, "measurement.read")
    return envelope(value)


@router.get("/dinh-nghia-do-luong/{definition_id}/xu-huong")
async def get_measurement_trend(
    definition_id: str,
    release_id: str = Query(default="", max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(
        await measurement_trend(database.value, definition_id, release_id or None, user)
    )


@router.get("/du-an/{project_id}/do-luong/so-sanh-ban-phat-hanh")
async def compare_measurement_releases_api(
    project_id: str,
    release_a: str = Query(min_length=1, max_length=200),
    release_b: str = Query(min_length=1, max_length=200),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(
        await compare_measurement_releases(database.value, project_id, release_a, release_b, user)
    )


@router.get("/du-an/{project_id}/do-luong/canh-bao")
async def list_measurement_threshold_alerts(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await measurement_alerts(database.value, project_id, user))


@router.get("/dinh-nghia-do-luong/{definition_id}/xac-thuc")
async def validate_measurement_definition(
    definition_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await validate_definition(database.value, definition_id, user))


@router.put("/dinh-nghia-do-luong/{definition_id}/ghim")
async def pin_measurement_to_dashboard(
    definition_id: str, payload: MetricDashboardPin, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await pin_metric(database.value, definition_id, payload, user))


@router.get("/dinh-nghia-do-luong/{definition_id}/xuat")
async def export_measurement_data(
    definition_id: str, user: CurrentUser = Depends(get_current_user)
):
    definition = await database.value.measurement_definitions.find_one({"_id": definition_id})
    if not definition:
        raise HTTPException(status_code=404, detail={"code": "ENTITY_NOT_FOUND"})
    from src.core.common import get_project

    await get_project(definition["project_id"], user, "report.export")
    snapshots = (
        await database.value.measurement_snapshots.find(
            {"project_id": definition["project_id"], "measurement_key": definition["key"]}
        )
        .sort("measured_at", 1)
        .to_list(10000)
    )
    content = export_metric_csv(definition, snapshots)
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="metric-{definition["key"]}.csv"'},
    )
