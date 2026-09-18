from fastapi import APIRouter, Depends, HTTPException, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.core.database import database
from src.domain.environment_incident import (
    EnvironmentIncidentCreate,
    EnvironmentIncidentPatch,
    EnvironmentIncidentTransition,
)
from src.services.environment_incident import (
    create_incident,
    get_incident,
    list_incidents,
    transition_incident,
    update_incident,
)

router = APIRouter(prefix="/kiem-thu", tags=["Incident môi trường"])


@router.get("/du-an/{project_id}/su-co-moi-truong")
async def list_environment_incidents(
    project_id: str,
    environment_id: str = Query(default=""),
    status: str = Query(default=""),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await list_incidents(database.value, project_id, environment_id, status, user))


@router.post("/du-an/{project_id}/su-co-moi-truong", status_code=201)
async def create_environment_incident(
    project_id: str,
    payload: EnvironmentIncidentCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await create_incident(database.value, project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/su-co-moi-truong/{incident_id}")
async def get_environment_incident(incident_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await get_incident(database.value, incident_id, user)
    return envelope(value, revision=value["revision"])


@router.patch("/su-co-moi-truong/{incident_id}")
async def patch_environment_incident(
    incident_id: str,
    payload: EnvironmentIncidentPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await update_incident(database.value, incident_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/su-co-moi-truong/{incident_id}/dieu-tra")
async def investigate_environment_incident(
    incident_id: str,
    payload: EnvironmentIncidentTransition,
    user: CurrentUser = Depends(get_current_user),
):
    if payload.status == "CLOSED":
        raise HTTPException(status_code=422, detail={"code": "USE_INCIDENT_CLOSE_ENDPOINT"})
    value = await transition_incident(database.value, incident_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/su-co-moi-truong/{incident_id}/ket-thuc")
async def close_environment_incident(
    incident_id: str,
    payload: EnvironmentIncidentTransition,
    user: CurrentUser = Depends(get_current_user),
):
    if payload.status != "CLOSED":
        raise HTTPException(status_code=422, detail={"code": "INCIDENT_CLOSE_STATUS_REQUIRED"})
    value = await transition_incident(database.value, incident_id, payload, user)
    return envelope(value, revision=value["revision"])
