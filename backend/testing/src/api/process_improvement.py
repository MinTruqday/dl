from fastapi import APIRouter, Depends

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.process_improvement import (
    ProcessImprovementCreate,
    ProcessImprovementEvaluation,
    ProcessImprovementLink,
    ProcessImprovementMetrics,
    ProcessImprovementPatch,
    ProcessImprovementTransition,
    StatisticalBaselineCreate,
    StatisticalComparison,
    StatisticalSpecialCause,
)
from src.services.process_improvement import ProcessImprovementService

router = APIRouter(prefix="/kiem-thu", tags=["Cải tiến quy trình và kiểm soát thống kê"])


@router.get("/du-an/{project_id}/cai-tien-quy-trinh")
async def list_process_improvements(project_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await ProcessImprovementService.list(project_id, user))


@router.post("/du-an/{project_id}/cai-tien-quy-trinh", status_code=201)
async def create_process_improvement(
    project_id: str,
    payload: ProcessImprovementCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.create(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/cai-tien-quy-trinh/{proposal_id}")
async def get_process_improvement(proposal_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await ProcessImprovementService.get(proposal_id, user)
    return envelope(value, revision=value["revision"])


@router.patch("/cai-tien-quy-trinh/{proposal_id}")
async def patch_process_improvement(
    proposal_id: str,
    payload: ProcessImprovementPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.update(proposal_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/cai-tien-quy-trinh/{proposal_id}/lien-ket-nguon")
async def link_process_improvement_sources(
    proposal_id: str, payload: ProcessImprovementLink, user: CurrentUser = Depends(get_current_user)
):
    value = await ProcessImprovementService.link_sources(proposal_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/cai-tien-quy-trinh/{proposal_id}/phe-duyet-thu-nghiem")
async def approve_process_improvement_experiment(
    proposal_id: str,
    payload: ProcessImprovementTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.transition_action(
        proposal_id, payload, user, "approve"
    )
    return envelope(value, revision=value["revision"])


@router.post("/cai-tien-quy-trinh/{proposal_id}/duong-co-so")
async def record_process_improvement_baseline(
    proposal_id: str,
    payload: ProcessImprovementMetrics,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.record_baseline(proposal_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/cai-tien-quy-trinh/{proposal_id}/bat-dau")
async def start_process_improvement_experiment(
    proposal_id: str,
    payload: ProcessImprovementTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.transition_action(
        proposal_id, payload, user, "start"
    )
    return envelope(value, revision=value["revision"])


@router.post("/cai-tien-quy-trinh/{proposal_id}/danh-gia")
async def evaluate_process_improvement(
    proposal_id: str,
    payload: ProcessImprovementEvaluation,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.evaluate(proposal_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/cai-tien-quy-trinh/{proposal_id}/ap-dung")
async def adopt_process_improvement(
    proposal_id: str,
    payload: ProcessImprovementTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.transition_action(
        proposal_id, payload, user, "adopt"
    )
    return envelope(value, revision=value["revision"])


@router.post("/cai-tien-quy-trinh/{proposal_id}/tu-choi")
async def reject_process_improvement(
    proposal_id: str,
    payload: ProcessImprovementTransition,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.transition_action(
        proposal_id, payload, user, "reject"
    )
    return envelope(value, revision=value["revision"])


@router.get("/du-an/{project_id}/kiem-soat-thong-ke")
async def list_statistical_quality_analyses(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await ProcessImprovementService.list_statistical(project_id, user))


@router.post("/du-an/{project_id}/kiem-soat-thong-ke", status_code=201)
async def calculate_statistical_quality_baseline(
    project_id: str,
    payload: StatisticalBaselineCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.create_statistical(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/kiem-soat-thong-ke/{analysis_id}")
async def get_statistical_quality_analysis(
    analysis_id: str, user: CurrentUser = Depends(get_current_user)
):
    value = await ProcessImprovementService.get_statistical(analysis_id, user)
    return envelope(value, revision=value["revision"])


@router.post("/kiem-soat-thong-ke/{analysis_id}/nguyen-nhan-dac-biet")
async def annotate_statistical_special_cause(
    analysis_id: str,
    payload: StatisticalSpecialCause,
    user: CurrentUser = Depends(get_current_user),
):
    value = await ProcessImprovementService.annotate_special_cause(
        analysis_id, payload, user
    )
    return envelope(value, revision=value["revision"])


@router.post("/du-an/{project_id}/kiem-soat-thong-ke/so-sanh")
async def compare_statistical_quality(
    project_id: str, payload: StatisticalComparison, user: CurrentUser = Depends(get_current_user)
):
    return envelope(
        await ProcessImprovementService.compare_statistical(project_id, payload, user)
    )
