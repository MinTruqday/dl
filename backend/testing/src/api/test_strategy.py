from fastapi import APIRouter, Depends, Query

from src.core.auth import CurrentUser, get_current_user
from src.core.common import envelope
from src.domain.test_strategy import StrategyTransitionInput, StrategyVersionInput, TestStrategyCreate, TestStrategyPatch
from src.services.test_strategy_service import approve_strategy, archive_strategy, create_strategy, create_strategy_version, get_strategy_for_user, list_strategies, request_strategy_changes, submit_strategy, update_strategy


router = APIRouter(prefix="/kiem-thu", tags=["Quản trị kiểm thử"])


@router.get("/du-an/{project_id}/chien-luoc")
async def list_test_strategies(
    project_id: str,
    q: str = Query(default="", max_length=300),
    status: str = Query(default="", pattern="^(DRAFT|IN_REVIEW|APPROVED|SUPERSEDED|ARCHIVED)?$"),
    version: int | None = Query(default=None, ge=1),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    user: CurrentUser = Depends(get_current_user),
):
    return envelope(await list_strategies(project_id, user, q, status, version, page, page_size))


@router.post("/du-an/{project_id}/chien-luoc", status_code=201)
async def create_test_strategy(
    project_id: str,
    payload: TestStrategyCreate,
    user: CurrentUser = Depends(get_current_user),
):
    value = await create_strategy(project_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.get("/chien-luoc/{strategy_id}")
async def get_test_strategy(
    strategy_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    value = await get_strategy_for_user(strategy_id, user)
    return envelope(value, revision=value["revision"])


@router.patch("/chien-luoc/{strategy_id}")
async def patch_test_strategy(
    strategy_id: str,
    payload: TestStrategyPatch,
    user: CurrentUser = Depends(get_current_user),
):
    value = await update_strategy(strategy_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/chien-luoc/{strategy_id}/gui-ra-soat")
async def submit_test_strategy_review(
    strategy_id: str,
    payload: StrategyTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    value = await submit_strategy(strategy_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/chien-luoc/{strategy_id}/yeu-cau-chinh-sua")
async def request_test_strategy_changes(
    strategy_id: str,
    payload: StrategyTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    value = await request_strategy_changes(strategy_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/chien-luoc/{strategy_id}/phe-duyet")
async def approve_test_strategy(
    strategy_id: str,
    payload: StrategyTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    value = await approve_strategy(strategy_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/chien-luoc/{strategy_id}/tao-phien-ban", status_code=201)
async def version_test_strategy(
    strategy_id: str,
    payload: StrategyVersionInput,
    user: CurrentUser = Depends(get_current_user),
):
    value = await create_strategy_version(strategy_id, payload, user)
    return envelope(value, revision=value["revision"])


@router.post("/chien-luoc/{strategy_id}/luu-tru")
async def archive_test_strategy(
    strategy_id: str,
    payload: StrategyTransitionInput,
    user: CurrentUser = Depends(get_current_user),
):
    value = await archive_strategy(strategy_id, payload, user)
    return envelope(value, revision=value["revision"])
