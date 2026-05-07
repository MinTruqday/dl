from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import require_role, get_current_user
from models.user import UserInDB, RoleEnum
from core.response import APIResponse
from services.document import DocumentService
from pydantic import BaseModel

router = APIRouter(prefix="/ban-nhap")

class ModerateDocumentRequest(BaseModel):
    action: str
    reason: str

@router.get("/hang-doi", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_approval_queue(skip: int = 0, limit: int = 30):
    return APIResponse(
        data=await DocumentService.get_approval_queue(skip, limit),
        message="Lấy hàng đợi phê duyệt thành công"
    )

@router.post("/{document_id}/kiem-duyet", response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def moderate_document(document_id: str, req: ModerateDocumentRequest, current_user: UserInDB = Depends(get_current_user)):
    return APIResponse(
        data=await DocumentService.moderate_document(document_id, req.action, req.reason, current_user),
        message="Xử lý tài liệu thành công"
    )
