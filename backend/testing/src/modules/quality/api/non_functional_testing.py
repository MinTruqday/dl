from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.non_functional_test import (
    ExternalTestEvidenceImport,
    NonFunctionalTestPlanCreate,
    NonFunctionalTestPlanPatch,
    NonFunctionalTransition,
)
from src.services.non_functional_test import NonFunctionalTestService

router = APIRouter(prefix="/kiem-thu", tags=["Kiểm thử phi chức năng"])


@router.get("/du-an/{project_id}/ke-hoach-phi-chuc-nang")
async def list_non_functional_test_plans(
    project_id: str,
    plan_type: str = Query(default=""),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await NonFunctionalTestService.list(project_id, plan_type, user))


@router.post("/du-an/{project_id}/ke-hoach-phi-chuc-nang", status_code=201)
async def create_non_functional_test_plan(
    project_id: str,
    payload: NonFunctionalTestPlanCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await NonFunctionalTestService.create(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/ke-hoach-phi-chuc-nang/{plan_id}")
async def get_non_functional_test_plan(plan_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await NonFunctionalTestService.get(plan_id, user)
    return envelope(value, revision=value["revision"])


@router.patch("/ke-hoach-phi-chuc-nang/{plan_id}")
async def patch_non_functional_test_plan(
    plan_id: str, payload: NonFunctionalTestPlanPatch, user: CurrentUser = Depends(get_current_user)
):
    value = await NonFunctionalTestService.update(plan_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/ke-hoach-phi-chuc-nang/{plan_id}/gui-ra-soat")
async def submit_non_functional_test_plan(
    plan_id: str, payload: NonFunctionalTransition, user: CurrentUser = Depends(get_current_user)
):
    value = await NonFunctionalTestService.transition(plan_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/ke-hoach-phi-chuc-nang/{plan_id}/phe-duyet")
async def approve_non_functional_test_plan(
    plan_id: str, payload: NonFunctionalTransition, user: CurrentUser = Depends(get_current_user)
):
    value = await NonFunctionalTestService.transition(plan_id, payload, user, True)
    return envelope(value, revision=value["revision"])


@router.post("/ke-hoach-phi-chuc-nang/{plan_id}/bang-chung-ben-ngoai", status_code=201)
async def import_non_functional_test_evidence(
    plan_id: str, payload: ExternalTestEvidenceImport, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await NonFunctionalTestService.import_evidence(plan_id, payload, user))
