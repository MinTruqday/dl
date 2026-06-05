
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
from models.latex import CompileRequest, FormatRequest, ExportRequest, AutoSaveRequest
from services.latex import LatexService
from core.response import APIResponse
import time
router = APIRouter(prefix='/soan-thao-latex')

@router.delete('/don-dep', response_model=APIResponse[Any])
async def clean_temp_files(current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await LatexService.clean_temp_files(current_user, db=db), message='Dọn dẹp tập tin tạm thời thành công', status=200)

@router.post('/bien-dich-xem-truoc', response_model=Any)
async def compile_latex_preview(request: CompileRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    if len(request.model_dump_json()) > 50000:
        raise HTTPException(status_code=400, detail="Kích thước mã nguồn quá lớn (tối đa 50KB).")
    await check_rate_limit(str(current_user.id))
    pdf_bytes = await LatexService.compile_latex_preview(request, current_user, db=db)
    return Response(content=pdf_bytes, media_type='application/pdf')

@router.post('/dinh-dang', response_model=APIResponse[Any])
async def format_latex(request: FormatRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await LatexService.format_latex(request, db=db), message='Định dạng mã nguồn LaTeX thành công', status=200)

@router.post('/xuat-tai-lieu', response_model=Any)
async def export_latex(request: ExportRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    if len(request.model_dump_json()) > 50000:
        raise HTTPException(status_code=400, detail="Kích thước mã nguồn quá lớn (tối đa 50KB).")
    await check_rate_limit(str(current_user.id))
    file_bytes = await LatexService.export_latex(request, current_user, db=db)
    media_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' if request.format == 'docx' else 'text/html'
    return Response(content=file_bytes, media_type=media_type, headers={'Content-Disposition': f'attachment; filename=export.{request.format}'})

@router.post('/tu-dong-luu', response_model=APIResponse[Any])
async def cloud_auto_save(request: AutoSaveRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    return APIResponse(data=await LatexService.auto_save(request, db=db), message='Tự động lưu mã nguồn thành công', status=200)

@router.post('/xuat-zip', response_model=Any)
async def export_project_zip(request: CompileRequest, current_user: UserInDB=Depends(require_role([RoleEnum.AUTHOR, RoleEnum.ADMIN])), db=Depends(get_db)):
    await check_rate_limit(str(current_user.id))
    zip_bytes = await LatexService.export_project_zip(request, db=db)
    headers = {'Content-Disposition': 'attachment; filename="doclib_project.zip"'}
    return Response(zip_bytes, media_type='application/x-zip-compressed', headers=headers)