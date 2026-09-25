from fastapi import APIRouter, Depends

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import PerformancePlanDraftInput, SecurityTestSuggestionInput
from src.services.design_suggestion import DesignSuggestionService

router = APIRouter(prefix="/kiem-thu", tags=["Thiết kế kiểm thử chuyên sâu"])


@router.get("/du-an/{project_id}/ai/goi-y-kiem-thu-bao-mat")
async def list_security_test_suggestions(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await DesignSuggestionService.list_security(project_id, user))


@router.post("/du-an/{project_id}/ai/goi-y-kiem-thu-bao-mat", status_code=201)
async def generate_security_test_suggestions(
    project_id: str,
    payload: SecurityTestSuggestionInput,
    user: CurrentUser = Depends(get_current_user),
):
    value, metadata = await DesignSuggestionService.generate_security(project_id, payload, user)
    return envelope(value, revision=value["revision"], **metadata)


@router.get("/du-an/{project_id}/ai/ke-hoach-hieu-nang")
async def list_performance_plan_drafts(
    project_id: str, user: CurrentUser = Depends(get_current_user)
):
    return envelope(await DesignSuggestionService.list_performance(project_id, user))


@router.post("/du-an/{project_id}/ai/ke-hoach-hieu-nang", status_code=201)
async def generate_performance_plan_draft(
    project_id: str,
    payload: PerformancePlanDraftInput,
    user: CurrentUser = Depends(get_current_user),
):
    value, metadata = await DesignSuggestionService.generate_performance(project_id, payload, user)
    return envelope(value, revision=value["revision"], **metadata)
