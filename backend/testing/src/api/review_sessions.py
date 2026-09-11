from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.core.database import database
from src.domain.review_session import ReviewFindingCreate, ReviewFindingPatch, ReviewSessionCreate, ReviewSessionPatch, ReviewTransition
from src.services.review_session_service import add_finding, create_review, get_review, list_reviews, transition_review, update_finding, update_review


router = APIRouter(prefix="/kiem-thu", tags=["Rà soát chính thức"])


@router.get("/du-an/{project_id}/phien-ra-soat")
async def list_review_sessions(project_id: str, status: str = Query(default=""), artifact_type: str = Query(default=""), user: CurrentUser = Depends(get_current_user)):
    return envelope(await list_reviews(database.value, project_id, user, status, artifact_type))


@router.post("/du-an/{project_id}/phien-ra-soat", status_code=201)
async def create_review_session(project_id: str, payload: ReviewSessionCreate, user: CurrentUser = Depends(get_current_user)):
    value = await create_review(database.value, project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/phien-ra-soat/{review_id}")
async def get_review_session(review_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await get_review(database.value, review_id, user)
    value["findings"] = await database.value.review_findings.find({"review_session_id": review_id}).sort("created_at", 1).to_list(1000)
    return envelope(value, revision=value["revision"])


@router.patch("/phien-ra-soat/{review_id}")
async def patch_review_session(review_id: str, payload: ReviewSessionPatch, user: CurrentUser = Depends(get_current_user)):
    value = await update_review(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/{review_id}/bat-dau")
async def start_review_session(review_id: str, payload: ReviewTransition, user: CurrentUser = Depends(get_current_user)):
    value = await transition_review(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/{review_id}/findings", status_code=201)
async def create_review_finding(review_id: str, payload: ReviewFindingCreate, user: CurrentUser = Depends(get_current_user)):
    value = await add_finding(database.value, review_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.patch("/phien-ra-soat/finding/{finding_id}")
async def patch_review_finding(finding_id: str, payload: ReviewFindingPatch, user: CurrentUser = Depends(get_current_user)):
    value = await update_finding(database.value, finding_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phien-ra-soat/{review_id}/hoan-tat")
async def complete_review_session(review_id: str, payload: ReviewTransition, user: CurrentUser = Depends(get_current_user)):
    value = await transition_review(database.value, review_id, payload, user, True)
    return envelope(value, revision=value["revision"])
