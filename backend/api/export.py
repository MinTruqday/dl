from typing import Any, List, Optional
from fastapi import APIRouter, Depends, Query, Request, HTTPException, WebSocket, WebSocketDisconnect
from core.response import APIResponse
from api.dependency import get_current_user, require_role
from models.user import UserInDB, RoleEnum
from core.config import settings
import httpx
import websockets
import asyncio

CONTENT_URL = settings.CONTENT_SERVICE_URL
CONTENT_WS_URL = CONTENT_URL.replace("http://", "ws://").replace("https://", "wss://")

async def _proxy(method: str, path: str, **kwargs):
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            res = await client.request(method, f"{CONTENT_URL}{path}", **kwargs)
            if res.status_code >= 400:
                raise HTTPException(status_code=res.status_code, detail=res.json().get("detail", "Lỗi"))
            return res.json()
        except HTTPException:
            raise
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Lỗi kết nối Content Service: {e}")

from models.user import UserInDB
router = APIRouter(prefix='/xuat-tai-lieu')
(prefix='/xuat-tai-lieu')

@router.get('/{document_id}/pdf', response_model=APIResponse[Any])
async def export_document_pdf(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    pdf_content = await ExportService.export_document_pdf_watermarked(document_id, current_user, db=db)
    headers = {'Content-Disposition': f'attachment; filename="DocLib_Export_{document_id}_Watermarked.pdf"'}
    return APIResponse(data=Response(content=pdf_content, media_type='application/pdf', headers=headers), message='Xuất bản sao PDF đính kèm dấu bản quyền thành công', status=200)


@router.get('/{document_id}/docx', response_model=APIResponse[Any])
async def export_document_docx(document_id: str, current_user: UserInDB=Depends(get_current_user), db=Depends(get_db)):
    from core.database import db_client
    from services.compilation import CompilationService
    from fastapi import HTTPException
    db = db_client.mongodb.get_default_database()
    document = await db['documents'].find_one({'_id': document_id})
    if not document:
        raise HTTPException(status_code=404, detail='Không tìm thấy tài liệu.')
    content = document.get('content', '')
    docx_content = await CompilationService.export_to_format(content, 'docx', db=db)
    headers = {'Content-Disposition': f'attachment; filename="DocLib_{document_id}.docx"'}
    return APIResponse(data=Response(content=docx_content, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', headers=headers), message='Xuất bản sao Word thành công', status=200)