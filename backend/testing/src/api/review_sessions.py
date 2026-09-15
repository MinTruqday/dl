from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.core.database import database
from src.domain.review_session import (
    ReviewDecision,
    ReviewerAssignment,
    ReviewFindingAssignment,
    ReviewFindingCreate,
    ReviewFindingResolution,
    ReviewFindingVerification,
    ReviewFollowUpCreate,
    ReviewSessionCreate,
    ReviewSessionPatch,
    ReviewTerminalTransition,
    ReviewTransition,
)
from src.services.review_session import (
    add_finding,
    assign_finding,
    assign_reviewers,
    create_follow_up_review,
    create_review,
    get_review,
    list_reviews,
    record_review_decision,
    resolve_finding,
    review_metrics,
    transition_review,
    transition_review_terminal,
    update_review,
    verify_finding,
)
from src.services.review_session_export import export_review_csv

router = APIRouter(prefix="/kiem-thu", tags=["Rà soát chính thức"])


@router.get("/du-an/{project_id}/phien-ra-soat")
async def list_review_sessions(
    project_id: str,
    status: str = Query(default=""),
    artifact_type: str = Query(default=""),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await list_reviews(database.value, project_id, user, status, artifact_type))


@router.post("/du-an/{project_id}/phien-ra-soat", status_code=201)
async def create_review_session(
    project_id: str, payload: ReviewSessionCreate, user: CurrentUser = Depends(get_current_user)
):
    value = await create_review(database.value, project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/phien-ra-soat/{review_id}")
async def get_review_session(review_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await get_review(database.value, review_id, user)
    value["findings"] = (
        await database.value.review_findings.find({"review_session_id": review_id})
        .sort("created_at", 1)
        .to_list(1000)
    )
    return envelope(value, revision=value["revision"])


@router.patch("/phien-ra-soat/{review_id}")
async def patch_review_session(
    review_id: str, payload: ReviewSessionPatch, user: CurrentUser = Depends(get_current_user)
):
    value = await update_review(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.put("/phien-ra-soat/{review_id}/nguoi-ra-soat")
async def assign_review_session_reviewers(
    review_id: str, payload: ReviewerAssignment, user: CurrentUser = Depends(get_current_user)
):
    value = await assign_reviewers(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/{review_id}/bat-dau")
async def start_review_session(
    review_id: str, payload: ReviewTransition, user: CurrentUser = Depends(get_current_user)
):
    value = await transition_review(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/{review_id}/ket-qua", status_code=201)
async def create_review_finding(
    review_id: str, payload: ReviewFindingCreate, user: CurrentUser = Depends(get_current_user)
):
    value = await add_finding(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/ket-qua/{finding_id}/gan")
async def assign_review_finding(
    finding_id: str, payload: ReviewFindingAssignment, user: CurrentUser = Depends(get_current_user)
):
    value = await assign_finding(database.value, finding_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/ket-qua/{finding_id}/giai-quyet")
async def resolve_review_finding(
    finding_id: str, payload: ReviewFindingResolution, user: CurrentUser = Depends(get_current_user)
):
    value = await resolve_finding(database.value, finding_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/ket-qua/{finding_id}/xac-minh")
async def verify_review_finding(
    finding_id: str,
    payload: ReviewFindingVerification,
    user: CurrentUser = Depends(get_current_user),
):
    value = await verify_finding(database.value, finding_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/{review_id}/quyet-dinh")
async def record_review_session_decision(
    review_id: str, payload: ReviewDecision, user: CurrentUser = Depends(get_current_user)
):
    value = await record_review_decision(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/{review_id}/hoan-tat")
async def complete_review_session(
    review_id: str, payload: ReviewTransition, user: CurrentUser = Depends(get_current_user)
):
    value = await transition_review(database.value, review_id, payload, user, True)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/{review_id}/trang-thai-cuoi")
async def transition_review_session_terminal(
    review_id: str, payload: ReviewTerminalTransition, user: CurrentUser = Depends(get_current_user)
):
    value = await transition_review_terminal(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/phien-ra-soat/{review_id}/so-lieu")
async def get_review_session_metrics(review_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await get_review(database.value, review_id, user)
    return envelope(await review_metrics(database.value, value))


@router.post("/phien-ra-soat/{review_id}/phien-tiep-theo", status_code=201)
async def create_follow_up_review_session(
    review_id: str, payload: ReviewFollowUpCreate, user: CurrentUser = Depends(get_current_user)
):
    value = await create_follow_up_review(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/phien-ra-soat/{review_id}/xuat")
async def export_review_session(review_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await get_review(database.value, review_id, user)
    value = {
        **value,
        "findings": await database.value.review_findings.find({"review_session_id": review_id})
        .sort("created_at", 1)
        .to_list(1000),
    }
    content = export_review_csv(value)
    return StreamingResponse(
        iter([content]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="formal-review-{review_id}.csv"'},
    )
