from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.core.database import database
from src.domain.quality_evaluation import (
    QualityEvaluationCreate,
    QualityEvaluationPatch,
    QualityEvaluationReview,
    QualityEvaluationTransition,
    QualityWaiverCreate,
    QualityWaiverDecision,
)
from src.services.quality_evaluation import (
    add_waiver,
    approve_evaluation,
    create_evaluation,
    decide_waiver,
    get_evaluation,
    list_evaluations,
    review_evaluation,
    submit_evaluation,
    update_evaluation,
)

router = APIRouter(prefix="/kiem-thu", tags=["Đánh giá chất lượng sản phẩm"])


@router.get("/du-an/{project_id}/danh-gia-chat-luong")
async def list_quality_evaluations(
    project_id: str,
    release_id: str = Query(default=""),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await list_evaluations(database.value, project_id, release_id, user))


@router.post("/du-an/{project_id}/danh-gia-chat-luong", status_code=201)
async def create_quality_evaluation(
    project_id: str, payload: QualityEvaluationCreate, user: CurrentUser = Depends(get_current_user)
):
    value = await create_evaluation(database.value, project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/danh-gia-chat-luong/{evaluation_id}")
async def get_quality_evaluation(evaluation_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await get_evaluation(database.value, evaluation_id, user)
    return envelope(value, revision=value["revision"])


@router.patch("/danh-gia-chat-luong/{evaluation_id}")
async def patch_quality_evaluation(
    evaluation_id: str,
    payload: QualityEvaluationPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await update_evaluation(database.value, evaluation_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/danh-gia-chat-luong/{evaluation_id}/gui-ra-soat")
async def submit_quality_evaluation(
    evaluation_id: str,
    payload: QualityEvaluationTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await submit_evaluation(database.value, evaluation_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/danh-gia-chat-luong/{evaluation_id}/ra-soat")
async def review_quality_evaluation(
    evaluation_id: str,
    payload: QualityEvaluationReview,
    user: CurrentUser = Depends(get_current_user),
):
    value = await review_evaluation(database.value, evaluation_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/danh-gia-chat-luong/{evaluation_id}/mien-tru", status_code=201)
async def create_quality_waiver(
    evaluation_id: str, payload: QualityWaiverCreate, user: CurrentUser = Depends(get_current_user)
):
    value = await add_waiver(database.value, evaluation_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/danh-gia-chat-luong/{evaluation_id}/mien-tru/{waiver_id}/quyet-dinh")
async def decide_quality_waiver(
    evaluation_id: str,
    waiver_id: str,
    payload: QualityWaiverDecision,
    user: CurrentUser = Depends(get_current_user),
):
    value = await decide_waiver(database.value, evaluation_id, waiver_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/danh-gia-chat-luong/{evaluation_id}/phe-duyet")
async def approve_quality_evaluation(
    evaluation_id: str,
    payload: QualityEvaluationTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await approve_evaluation(database.value, evaluation_id, payload, user)
    return envelope(value, revision=value["revision"])
