from src.core.infrastructure.redis import redis
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from loguru import logger
from src.schemas.composition import CompileRequest
from src.engines.latex import LatexEngine
from src.core.dependency import RateLimiting, get_current_user, CurrentUser

router = APIRouter(prefix="/soan-thao/latex")

@router.post("/bien-dich", dependencies=[Depends(RateLimiting(10, 60))])
async def compile_latex(req: CompileRequest, current_user=Depends(get_current_user)):
    try:
        pdf_bytes = await LatexEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except ValueError:
        logger.warning("Rejected invalid LaTeX compilation request")
        raise HTTPException(
            status_code=400, detail="Quá trình biên dịch thất bại do lỗi cú pháp trong tài liệu"
        )

@router.post("/ket-xuat/{format}", dependencies=[Depends(RateLimiting(10, 60))])
async def export_document(format: str, req: CompileRequest, current_user=Depends(get_current_user)):
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
    except ValueError:
        logger.warning("Rejected invalid LaTeX export request")
        raise HTTPException(status_code=400, detail="Quá trình xuất dữ liệu tài liệu gặp sự cố")

@router.post("/dinh-dang")
async def format_latex(req: CompileRequest, current_user=Depends(get_current_user)):
    return LatexEngine.format_latex(req.content)

@router.post("/ket-xuat-zip")
async def export_project_zip(req: CompileRequest, current_user=Depends(get_current_user)):
    zip_bytes = LatexEngine.export_project_zip(req.content)
    return Response(content=zip_bytes, media_type="application/x-zip-compressed")

@router.delete("/don-dep")
async def clean_temp_files(current_user: CurrentUser = Depends(get_current_user)):
    if redis:
        await redis.delete(f"latex_draft:{current_user.id}")
    return {"message": "Thực hiện thao tác dọn dẹp tập tin tạm thời hoàn tất", "data": {}}

@router.post("/tu-dong-luu")
async def auto_save_latex(payload: CompileRequest, current_user: CurrentUser = Depends(get_current_user)):
    if redis:
        content = payload.content
        if content:
            await redis.setex(f"latex_draft:{current_user.id}", 604800, content)
    return {"message": "Thực hiện thao tác lưu tự động bản nháp hoàn tất", "data": {}}

@router.get("/ban-nhap")
async def get_latex_draft(current_user: CurrentUser = Depends(get_current_user)):
    if redis:
        draft = await redis.get(f"latex_draft:{current_user.id}")
        if draft:
            return {"message": "Trích xuất dữ liệu bản nháp hoàn tất", "data": {"content": draft.decode('utf-8') if isinstance(draft, bytes) else draft}}
    return {"message": "Thao tác hoàn tất: Không tìm thấy dữ liệu bản nháp", "data": {"content": None}}
