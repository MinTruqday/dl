from src.core.logging_route import LoggingRoute
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from loguru import logger
from src.schemas.composition import CompileRequest
from src.engines.editorjs import EditorjsEngine
from src.core.dependency import RateLimiting, get_current_user

router = APIRouter(route_class=LoggingRoute, prefix="/soan-thao/editorjs")

@router.post("/bien-dich", dependencies=[Depends(RateLimiting(10, 60))])
async def compile_editorjs(req: CompileRequest, current_user=Depends(get_current_user)):
    try:
        pdf_bytes = await EditorjsEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except ValueError:
        logger.warning("Rejected invalid EditorJS compilation request")
        raise HTTPException(status_code=400, detail="Quá trình biên dịch tài liệu thất bại")

@router.post("/ket-xuat/{format}", dependencies=[Depends(RateLimiting(10, 60))])
async def export_editorjs(
    format: str,
    req: CompileRequest,
    current_user=Depends(get_current_user),
):
    if format not in {"pdf", "docx", "html"}:
        raise HTTPException(status_code=400, detail="Định dạng xuất không được hỗ trợ")
    try:
        if format == "pdf":
            pdf_bytes = await EditorjsEngine.compile_to_pdf(req.content)
            return Response(content=pdf_bytes, media_type="application/pdf")
        out_bytes = await EditorjsEngine.export_to_format(req.content, format)
        media_type = "text/html" if format == "html" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return Response(content=out_bytes, media_type=media_type)
    except ValueError:
        logger.warning("Rejected invalid EditorJS export request")
        raise HTTPException(status_code=400, detail="Quá trình kết xuất tài liệu thất bại")
