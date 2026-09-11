from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.test_analysis import FindingResolutionInput, TestAnalysisAIInput, TestConditionCreate, TestConditionPatch, TestConditionTransition
from src.services.test_analysis_service import condition_coverage, create_condition, get_condition_for_user, list_conditions, resolve_finding, run_ai_analysis, transition_condition, update_condition


router = APIRouter(prefix="/kiem-thu", tags=["Phân tích kiểm thử"])


@router.get("/du-an/{project_id}/dieu-kien-kiem-thu")
async def list_test_conditions(
    project_id: str,
    q: str = Query(default="", max_length=300),
    status: str = Query(default="", max_length=30),
    risk: str = Query(default="", max_length=30),
    testability_status: str = Query(default="", max_length=40),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await list_conditions(project_id, user, q, status, risk, testability_status, page, page_size))


@router.post("/du-an/{project_id}/dieu-kien-kiem-thu", status_code=201)
async def create_test_condition(
    project_id: str,
    payload: TestConditionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await create_condition(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/dieu-kien-kiem-thu/{condition_id}")
async def get_test_condition(
    condition_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    value = await get_condition_for_user(condition_id, user)
    return envelope(value, revision=value["revision"])


@router.patch("/dieu-kien-kiem-thu/{condition_id}")
async def patch_test_condition(
    condition_id: str,
    payload: TestConditionPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await update_condition(condition_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/dieu-kien-kiem-thu/{condition_id}/gui-ra-soat")
async def submit_test_condition_review(
    condition_id: str,
    payload: TestConditionTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await transition_condition(condition_id, payload, user, "submit")
    return envelope(value, revision=value["revision"])


@router.post("/dieu-kien-kiem-thu/{condition_id}/phe-duyet")
async def approve_test_condition(
    condition_id: str,
    payload: TestConditionTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await transition_condition(condition_id, payload, user, "approve")
    return envelope(value, revision=value["revision"])


@router.post("/dieu-kien-kiem-thu/{condition_id}/luu-tru")
async def archive_test_condition(
    condition_id: str,
    payload: TestConditionTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await transition_condition(condition_id, payload, user, "archive")
    return envelope(value, revision=value["revision"])


@router.post("/dieu-kien-kiem-thu/{condition_id}/ket-qua/{finding_id}/giai-quyet")
async def resolve_test_analysis_finding(
    condition_id: str,
    finding_id: str,
    payload: FindingResolutionInput,
    user: CurrentUser = Depends(get_current_user),
):
    value = await resolve_finding(condition_id, finding_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/du-an/{project_id}/phan-tich-kiem-thu/ai", status_code=201)
async def run_test_analysis_ai(
    project_id: str,
    payload: TestAnalysisAIInput,
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await run_ai_analysis(project_id, payload, user))


@router.get("/du-an/{project_id}/phan-tich-kiem-thu/truy-vet")
async def get_test_condition_coverage(
    project_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await condition_coverage(project_id, user))
