from typing import Any
from fastapi import APIRouter, Depends
from api.dependency import get_db, require_role, get_current_user
from models.user import UserInDB, RoleEnum
from models.document import ModerateDocumentRequest
from core.response import APIResponse
from services.document import DocumentService
router = APIRouter(prefix='/ban-nhap')

@router.get('/hang-doi', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def get_approval_queue(cursor: str=None, limit: int=30, db=Depends(get_db)):
    return APIResponse(data=await DocumentService.get_approval_queue(cursor, limit, db=db), message='Lấy hàng đợi phê duyệt thành công')

@router.post('/{document_id}/kiem-duyet', response_model=APIResponse[Any], dependencies=[Depends(require_role([RoleEnum.MODERATOR, RoleEnum.ADMIN]))])
async def moderate_document(document_id: str, req: ModerateDocumentRequest, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    return APIResponse(data=await DocumentService.moderate_document(document_id, req.action, req.reason, current_user, db=db), message='Xử lý tài liệu thành công')