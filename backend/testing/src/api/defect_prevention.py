from fastapi import APIRouter, Depends

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.core.database import database
from src.domain.causal_analysis import CausalAiRequest, CausalAnalysisCreate, CausalAnalysisPatch, CausalApproval, CausalTransition, PreventionActionCreate, PreventionActionPatch
from src.services.causal_analysis_service import approve_root_cause, create_action, create_analysis, generate_hypotheses, get_analysis, list_analyses, transition_analysis, update_action, update_analysis


router = APIRouter(prefix="/kiem-thu", tags=["Phòng ngừa lỗi"])


@router.get("/du-an/{project_id}/phan-tich-nguyen-nhan")
async def list_causal_analyses(project_id: str, user: CurrentUser = Depends(get_current_user)):
    return envelope(await list_analyses(database.value, project_id, user))


@router.post("/du-an/{project_id}/phan-tich-nguyen-nhan", status_code=201)
async def create_causal_analysis(project_id: str, payload: CausalAnalysisCreate, user: CurrentUser = Depends(get_current_user)):
    value = await create_analysis(database.value, project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/phan-tich-nguyen-nhan/{analysis_id}")
async def get_causal_analysis(analysis_id: str, user: CurrentUser = Depends(get_current_user)):
    value = await get_analysis(database.value, analysis_id, user)
    value["actions"] = await database.value.preventive_actions.find({"causal_analysis_id": analysis_id}).sort("created_at", 1).to_list(1000)
    return envelope(value, revision=value["revision"])


@router.patch("/phan-tich-nguyen-nhan/{analysis_id}")
async def patch_causal_analysis(analysis_id: str, payload: CausalAnalysisPatch, user: CurrentUser = Depends(get_current_user)):
    value = await update_analysis(database.value, analysis_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phan-tich-nguyen-nhan/{analysis_id}/phe-duyet-nguyen-nhan")
async def approve_causal_root_cause(analysis_id: str, payload: CausalApproval, user: CurrentUser = Depends(get_current_user)):
    value = await approve_root_cause(database.value, analysis_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phan-tich-nguyen-nhan/{analysis_id}/hanh-dong", status_code=201)
async def create_prevention_action(analysis_id: str, payload: PreventionActionCreate, user: CurrentUser = Depends(get_current_user)):
    value = await create_action(database.value, analysis_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.patch("/hanh-dong-phong-ngua/{action_id}")
async def patch_prevention_action(action_id: str, payload: PreventionActionPatch, user: CurrentUser = Depends(get_current_user)):
    value = await update_action(database.value, action_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phan-tich-nguyen-nhan/{analysis_id}/trang-thai")
async def transition_causal_analysis(analysis_id: str, payload: CausalTransition, user: CurrentUser = Depends(get_current_user)):
    value = await transition_analysis(database.value, analysis_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/phan-tich-nguyen-nhan/{analysis_id}/ai/goi-y")
async def generate_causal_analysis_hypotheses(analysis_id: str, payload: CausalAiRequest, user: CurrentUser = Depends(get_current_user)):
    return envelope(await generate_hypotheses(database.value, analysis_id, payload, user))
