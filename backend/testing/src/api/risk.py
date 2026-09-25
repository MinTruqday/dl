from fastapi import APIRouter, Depends

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.contracts import RiskRankingApproval, RiskRankingGenerate, RiskRankingPatch
from src.services.risk_ranking import RiskRankingService

router = APIRouter(prefix="/kiem-thu", tags=["Ưu tiên rủi ro"])


@router.get("/du-an/{project_id}/uu-tien-rui-ro", openapi_extra={"x-function-ids": ["RISK-01"]})
async def get_risk_ranking(project_id: str, user: CurrentUser = Depends(get_current_user)):
    ranking = await RiskRankingService.current(project_id, user)
    return envelope(ranking, revision=ranking.get("revision", 1))


@router.post(
    "/du-an/{project_id}/uu-tien-rui-ro",
    status_code=201,
    openapi_extra={"x-function-ids": ["RISK-02"]},
)
async def generate_risk_ranking(
    project_id: str, payload: RiskRankingGenerate, user: CurrentUser = Depends(get_current_user)
):
    ranking = await RiskRankingService.generate(project_id, payload, user)
    return envelope(ranking, revision=1)


@router.patch("/uu-tien-rui-ro/{ranking_id}", openapi_extra={"x-function-ids": ["RISK-03"]})
async def review_risk_ranking(
    ranking_id: str, payload: RiskRankingPatch, user: CurrentUser = Depends(get_current_user)
):
    updated = await RiskRankingService.review(ranking_id, payload, user)
    return envelope(updated, revision=updated["revision"])


@router.post(
    "/uu-tien-rui-ro/{ranking_id}/phe-duyet", openapi_extra={"x-function-ids": ["RISK-04"]}
)
async def approve_risk_ranking(
    ranking_id: str, payload: RiskRankingApproval, user: CurrentUser = Depends(get_current_user)
):
    updated = await RiskRankingService.approve(ranking_id, payload, user)
    return envelope(updated, revision=updated["revision"])
