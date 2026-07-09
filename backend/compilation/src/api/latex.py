from src.core.infrastructure.redis import redis
import httpx
from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import Response
from loguru import logger
from src.schemas.composition import CompileRequest
from src.engines.latex import LatexEngine
from src.core.dependency import get_current_user, get_current_user_optional, CurrentUser
from src.core.infrastructure.database import database

router = APIRouter(route_class=LoggingRoute, prefix="/soan-thao/latex")

@router.post("/bien-dich")
async def compile_latex(req: CompileRequest):
    try:
        pdf_bytes = await LatexEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        logger.exception("Failed to compile LaTeX content to requested format")
        raise HTTPException(
            status_code=400, detail="Quá trình biên dịch thất bại do lỗi cú pháp trong tài liệu"
        )

@router.post("/ket-xuat/{format}")
async def export_document(format: str, req: CompileRequest):
    if format not in ["docx", "html", "pdf"]:
        raise HTTPException(status_code=400, detail="Hệ thống không hỗ trợ định dạng xuất tài liệu yêu cầu")

    try:
        if format == "pdf":
            pdf_bytes = await LatexEngine.compile_to_pdf(req.content)
            return Response(content=pdf_bytes, media_type="application/pdf")
            
        file_bytes = await LatexEngine.export_to_format(req.content, format)

        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        if format == "html":
            media_type = "text/html"

        return Response(content=file_bytes, media_type=media_type)
    except Exception as e:
        logger.exception("Failed to export LaTeX content to requested format")
        raise HTTPException(status_code=500, detail="Quá trình xuất dữ liệu tài liệu gặp sự cố")

@router.post("/dinh-dang")
async def format_latex(req: CompileRequest):
    return LatexEngine.format_latex(req.content)

@router.post("/ket-xuat-zip")
async def export_project_zip(req: CompileRequest):
    zip_bytes = LatexEngine.export_project_zip(req.content)
    return Response(content=zip_bytes, media_type="application/x-zip-compressed")

@router.delete("/don-dep")
async def clean_temp_files(current_user: CurrentUser = Depends(get_current_user_optional)):
    if current_user and redis:
        await redis.delete(f"latex_draft:{current_user.id}")
    return {"message": "Thực hiện thao tác dọn dẹp tập tin tạm thời thành công", "data": {}}

@router.post("/tu-dong-luu")
async def auto_save_latex(payload: dict, current_user: CurrentUser = Depends(get_current_user)):
    if redis:
        content = payload.get("content", "")
        if content:
            await redis.setex(f"latex_draft:{current_user.id}", 604800, content)
    return {"message": "Thực hiện thao tác lưu tự động bản nháp thành công", "data": {}}

@router.get("/ban-nhap")
async def get_latex_draft(current_user: CurrentUser = Depends(get_current_user)):
    if redis:
        draft = await redis.get(f"latex_draft:{current_user.id}")
        if draft:
            return {"message": "Truy xuất dữ liệu bản nháp thành công", "data": {"content": draft.decode('utf-8') if isinstance(draft, bytes) else draft}}
    return {"message": "Thao tác thành công: Không tìm thấy dữ liệu bản nháp", "data": {"content": None}}
