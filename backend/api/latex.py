import time
from fastapi import HTTPException
from core.database import db_client

async def check_rate_limit(user_id: str, limit: int = 5, window: int = 60):
    if hasattr(db_client, 'redis') and db_client.redis:
        key = f"rl:latex:{user_id}"
        current = await db_client.redis.incr(key)
        if current == 1:
            await db_client.redis.expire(key, window)
        if current > limit:
            raise HTTPException(status_code=429, detail="Bạn đã thao tác quá nhanh. Vui lòng thử lại sau.")

from typing import Any
from core.response import APIResponse
from fastapi import APIRouter, Depends, Response
from models.user import UserInDB, RoleEnum
from api.dependency import get_db, require_role
from pydantic import BaseModel, Field

class CompileRequest(BaseModel):
    content: str = Field(..., max_length=100000)
    is_fragment: bool = False

class FormatRequest(BaseModel):
    content: str = Field(..., max_length=100000)

class ExportRequest(BaseModel):
    content: str = Field(..., max_length=100000)
    format: str = "docx"

class AutoSaveRequest(BaseModel):
    document_id: str
    content: str

import httpx
from core.config import settings
from datetime import datetime, timezone
import hashlib
import base64

COMPILER_URL = settings.COMPILER_URL

router = APIRouter(prefix='/soan-thao-latex')

@router.delete('/don-dep', response_model=APIResponse[Any])
async def clean_temp_files(current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data={'status': 'success', 'message': 'Dịch vụ biên dịch độc lập đã tự động dọn dẹp bộ nhớ', 'bytes_freed': 0}, message='Dọn dẹp tập tin tạm thời thành công', status=200)

@router.post('/bien-dich-xem-truoc', response_model=Any)
async def compile_latex_preview(request: CompileRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    if len(request.model_dump_json()) > 50000:
        raise HTTPException(status_code=400, detail="Kích thước mã nguồn quá lớn (tối đa 50KB).")
    await check_rate_limit(str(current_user.id))
    latex_code = request.content
    md5_hash = hashlib.md5(latex_code.encode('utf-8')).hexdigest()
    cache_key = f'latex_preview_{md5_hash}'
    if hasattr(db_client, 'redis') and db_client.redis:
        cached_b64 = await db_client.redis.get(cache_key)
        if cached_b64:
            return Response(content=base64.b64decode(cached_b64), media_type='application/pdf')
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            res = await client.post(f'{COMPILER_URL}/compile/latex/compile', json={'content': latex_code, 'is_fragment': request.is_fragment})
            if res.status_code == 200:
                if hasattr(db_client, 'redis') and db_client.redis:
                    b64_content = base64.b64encode(res.content).decode('utf-8')
                    await db_client.redis.set(cache_key, b64_content, ex=60)
                return Response(content=res.content, media_type='application/pdf')
            raise HTTPException(status_code=res.status_code, detail=res.json().get('detail', 'Lỗi kết nối tới dịch vụ biên dịch.'))
    except httpx.ReadTimeout:
        raise HTTPException(status_code=504, detail='Quá thời gian xử lý công thức LaTeX tại Compiler.')

@router.post('/dinh-dang', response_model=APIResponse[Any])
async def format_latex(request: FormatRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(f'{COMPILER_URL}/compile/latex/format', json={'content': request.content})
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get('detail', 'Lỗi hệ thống khi đang định dạng mã LaTeX.'))
        return APIResponse(data=res.json(), message='Định dạng mã nguồn LaTeX thành công', status=200)

@router.post('/xuat-tai-lieu', response_model=Any)
async def export_latex(request: ExportRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    if len(request.model_dump_json()) > 50000:
        raise HTTPException(status_code=400, detail="Kích thước mã nguồn quá lớn (tối đa 50KB).")
    if request.format not in ['docx', 'html']:
        raise HTTPException(status_code=400, detail='Định dạng không được hỗ trợ.')
    await check_rate_limit(str(current_user.id))
    async with httpx.AsyncClient(timeout=45.0) as client:
        res = await client.post(f'{COMPILER_URL}/compile/latex/export/{request.format}', json={'content': request.content})
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get('detail', 'Máy chủ biên dịch không thể tạo tập tin.'))
        media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if request.format == 'docx' else 'text/html'
        return Response(content=res.content, media_type=media_type, headers={'Content-Disposition': f'attachment; filename=export.{request.format}'})

@router.post('/tu-dong-luu', response_model=APIResponse[Any])
async def cloud_auto_save(request: AutoSaveRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    await db['documents'].update_one({'_id': request.document_id}, {'$set': {'content': request.content, 'updated_at': datetime.now(timezone.utc)}})
    return APIResponse(data={'status': 'success', 'timestamp': datetime.now(timezone.utc).isoformat()}, message='Tự động lưu mã nguồn thành công', status=200)

@router.post('/xuat-zip', response_model=Any)
async def export_project_zip(request: CompileRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    await check_rate_limit(str(current_user.id))
    async with httpx.AsyncClient(timeout=10.0) as client:
        res = await client.post(f'{COMPILER_URL}/compile/latex/export-zip', json={'content': request.content, 'is_fragment': request.is_fragment})
        if res.status_code != 200:
            raise HTTPException(status_code=res.status_code, detail=res.json().get('detail', 'Lỗi hệ thống trong quá trình xuất bản tập tin.'))
        headers = {'Content-Disposition': 'attachment; filename="doclib_project.zip"'}
        return Response(content=res.content, media_type='application/x-zip-compressed', headers=headers)
