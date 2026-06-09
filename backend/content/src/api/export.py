from typing import Any
from src.core.response import APIResponse
from fastapi import APIRouter, Depends, Response
from src.api.dependency import get_db, get_current_user
from src.schemas.user import UserInDB
from src.services.export import ExportService
from src.services.document import DocumentService
router = APIRouter(prefix='/xuat-tai-lieu')

@router.get('/{document_id}/pdf', response_model=APIResponse[Any])
async def export_document_pdf(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    pdf_content = await ExportService.export_document_pdf_watermarked(document_id, current_user, db=db)
    headers = {'Content-Disposition': f'attachment; filename="DocLib_Export_{document_id}_Watermarked.pdf"'}
    return APIResponse(data=Response(content=pdf_content, media_type='application/pdf', headers=headers), message='Xuất bản sao PDF đính kèm dấu bản quyền thành công', status=200)


@router.get('/{document_id}/docx', response_model=APIResponse[Any])
async def export_document_docx(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    from src.core.database import db_client
    from src.services.compilation import CompilationService
    from fastapi import HTTPException
    db = db_client.mongodb.get_default_database()
    document = await db['documents'].find_one({'_id': document_id})
    if not document:
        raise HTTPException(status_code=404, detail='Không tìm thấy tài liệu.')
    content = document.get('content', '')
    docx_content = await CompilationService.export_to_format(content, 'docx', db=db)
    headers = {'Content-Disposition': f'attachment; filename="DocLib_{document_id}.docx"'}
    return APIResponse(data=Response(content=docx_content, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', headers=headers), message='Xuất bản sao Word thành công', status=200)