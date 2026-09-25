from fastapi import APIRouter, Depends, Query

from src.core.dependency import verify_internal_token
from src.schemas.internal import AccountLookup
from src.services.internal_identity import InternalIdentityService

router = APIRouter(
    prefix="/xac-thuc/noi-bo",
    tags=["Nội bộ xác thực"],
    dependencies=[Depends(verify_internal_token)],
)


@router.post("/danh-tinh/tra-cuu", include_in_schema=False)
async def lookup_accounts(payload: AccountLookup):
    return {"data": await InternalIdentityService.lookup_accounts(payload.user_ids)}


@router.get("/danh-tinh/giai-quyet", include_in_schema=False)
async def resolve_account_reference(value: str = Query(min_length=1, max_length=320)):
    return {"data": await InternalIdentityService.resolve_reference(value)}


@router.get("/phien/{session_id}/nguoi-dung/{user_id}", include_in_schema=False)
async def validate_session(session_id: str, user_id: str):
    return {"data": await InternalIdentityService.validate_session(session_id, user_id)}


@router.get("/cau-hinh/chinh-sach-tao-du-an", include_in_schema=False)
async def project_creation_policy():
    return {"data": await InternalIdentityService.project_creation_policy()}


@router.get("/tai-khoan/{user_id}", include_in_schema=False)
async def get_account_by_id(user_id: str):
    return {"data": await InternalIdentityService.account_by_id(user_id)}


@router.get("/tai-khoan/thu-dien-tu/{email}", include_in_schema=False)
async def get_account_by_email(email: str):
    return {"data": await InternalIdentityService.account_by_email(email)}


@router.get("/bao-mat/{user_id}", include_in_schema=False)
async def get_security_state(user_id: str):
    return {"data": await InternalIdentityService.security_state(user_id)}
