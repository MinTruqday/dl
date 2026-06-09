from typing import Any
from fastapi import APIRouter, Depends
from src.api.dependency import get_db, require_role, get_current_user
from src.schemas.user import UserInDB, RoleEnum
from src.core.response import APIResponse
from src.services.audit import AuditService

router = APIRouter(prefix='/nhat-ky')

@router.get('/tat-ca', response_model=APIResponse[Any])
async def get_all_audit_logs(
    limit: int = 50,
    cursor: str = None,
    current_user: UserInDB = Depends(require_role([RoleEnum.ADMIN, RoleEnum.MODERATOR])),
    db=Depends(get_db)
):
    return APIResponse(data=await AuditService.get_audit_logs(limit=limit, cursor=cursor, db=db), message='Lấy nhật ký kiểm tra thành công')