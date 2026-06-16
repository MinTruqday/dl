from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from loguru import logger
from src.schemas.latex import CompileRequest
from src.services.latex_engine import LatexEngine

router = APIRouter()

@router.post("/bien-dich")
async def compile_latex(req: CompileRequest):
    try:
        pdf_bytes = await LatexEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception:
        logger.error("Lỗi khi truy xuất tài liệu")
        raise HTTPException(
            status_code=500, 
            detail="Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"
        )

@router.post("/ket-xuat/{format}")
async def export_document(format: str, req: CompileRequest):
    if format not in ["docx", "html"]:
        raise HTTPException(
            status_code=400, 
            detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
        )

    try:
        file_bytes = await LatexEngine.export_to_format(req.content, format)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if format == "html":
            media_type = "text/html"

        return Response(content=file_bytes, media_type=media_type)
    except Exception:
        logger.error("Lỗi khi truy xuất tài liệu")
        raise HTTPException(
            status_code=500, 
            detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
        )

@router.post("/dinh-dang")
async def format_latex(req: CompileRequest):
    return LatexEngine.format_latex(req.content)

@router.post("/ket-xuat-nen-tap-tin")
async def export_project_zip(req: CompileRequest):
    zip_bytes = LatexEngine.export_project_zip(req.content)
    return Response(content=zip_bytes, media_type="application/x-zip-compressed")