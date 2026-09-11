from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.test_completion import CompletionSignOff, CompletionTransition, ResidualRiskDecision, TestCompletionAiDraft, TestCompletionCreate, TestCompletionPatch
from src.services.test_completion_service import cluster_completion_lessons, create_completion_report, decide_residual_risk, generate_completion_narrative, get_completion_for_user, list_completion_reports, sign_off_completion, transition_completion, update_completion_report


router = APIRouter(prefix="/kiem-thu", tags=["Hoàn tất kiểm thử"])


@router.get("/du-an/{project_id}/hoan-tat-kiem-thu")
async def list_test_completion_reports(
    project_id: str,
    release_id: str = Query(default="", max_length=200),
    status: str = Query(default="", pattern="^(DRAFT|IN_REVIEW|APPROVED|CLOSED)?$"),
    limit: int = Query(default=200, ge=1, le=500),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await list_completion_reports(project_id, release_id or None, status or None, limit, user))


@router.post("/du-an/{project_id}/hoan-tat-kiem-thu", status_code=201)
async def create_test_completion_report(
    project_id: str,
    payload: TestCompletionCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await create_completion_report(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/hoan-tat-kiem-thu/{report_id}")
async def get_test_completion_report(report_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await get_completion_for_user(report_id, user)
    return envelope(value, revision=value["revision"])


@router.patch("/hoan-tat-kiem-thu/{report_id}")
async def patch_test_completion_report(
    report_id: str,
    payload: TestCompletionPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await update_completion_report(report_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/hoan-tat-kiem-thu/{report_id}/ai/ban-nhap")
async def draft_test_completion_narrative(
    report_id: str,
    payload: TestCompletionAiDraft,
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await generate_completion_narrative(report_id, payload, user))


@router.post("/hoan-tat-kiem-thu/{report_id}/ai/gom-bai-hoc")
async def cluster_test_completion_lessons(
    report_id: str,
    payload: TestCompletionAiDraft,
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await cluster_completion_lessons(report_id, payload, user))


@router.post("/hoan-tat-kiem-thu/{report_id}/gui-ra-soat")
async def submit_test_completion_review(
    report_id: str,
    payload: CompletionTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await transition_completion(report_id, payload, user, "DRAFT", "IN_REVIEW", "testcompletion.review", "test_completion_submitted")
    return envelope(value, revision=value["revision"])


@router.post("/hoan-tat-kiem-thu/{report_id}/yeu-cau-chinh-sua")
async def request_test_completion_changes(
    report_id: str,
    payload: CompletionTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await transition_completion(report_id, payload, user, "IN_REVIEW", "DRAFT", "testcompletion.review", "test_completion_changes_requested")
    return envelope(value, revision=value["revision"])


@router.post("/hoan-tat-kiem-thu/{report_id}/ky-xac-nhan")
async def sign_off_test_completion(
    report_id: str,
    payload: CompletionSignOff,
    user: CurrentUser = Depends(get_current_user),
):
    value = await sign_off_completion(report_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/hoan-tat-kiem-thu/{report_id}/rui-ro/{risk_id}/xu-ly")
async def decide_test_completion_residual_risk(
    report_id: str,
    risk_id: str,
    payload: ResidualRiskDecision,
    user: CurrentUser = Depends(get_current_user),
):
    value = await decide_residual_risk(report_id, risk_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/hoan-tat-kiem-thu/{report_id}/phe-duyet")
async def approve_test_completion_report(
    report_id: str,
    payload: CompletionTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await transition_completion(report_id, payload, user, "IN_REVIEW", "APPROVED", "testcompletion.approve", "test_completion_approved")
    return envelope(value, revision=value["revision"])


@router.post("/hoan-tat-kiem-thu/{report_id}/dong")
async def close_test_completion_report(
    report_id: str,
    payload: CompletionTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await transition_completion(report_id, payload, user, "APPROVED", "CLOSED", "testcompletion.close", "test_completion_closed")
    return envelope(value, revision=value["revision"])
