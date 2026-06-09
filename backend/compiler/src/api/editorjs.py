from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from src.schemas.editorjs import EditorJSCompileRequest
from src.services.editorjs_engine import EditorJSEngine
from loguru import logger

router = APIRouter()

@router.post("/bien-dich")
async def compile_editorjs_to_pdf(req: EditorJSCompileRequest):
    """Biên dịch EditorJS blocks → PDF qua LaTeX."""
    try:
        pdf_bytes = await EditorJSEngine.compile_to_pdf(
            content=req.content,
            title=req.title,
            author=req.author,
            font_size=req.font_size,
            paper_size=req.paper_size,
        )
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        logger.error(f"EditorJS compile error: {e}")
        if isinstance(e.args[0], dict):
            raise HTTPException(status_code=400, detail=e.args[0])
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/xuat/{format}")
async def export_editorjs(format: str, req: EditorJSCompileRequest):
    """Xuất EditorJS blocks sang DOCX hoặc HTML."""
    if format not in ["docx", "html"]:
        raise HTTPException(status_code=400, detail="Định dạng không hỗ trợ. Dùng: docx, html")
    try:
        file_bytes = await EditorJSEngine.export_to_format(
            content=req.content,
            target_format=format,
            title=req.title,
            author=req.author,
        )
        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            if format == "docx"
            else "text/html"
        )
        return Response(content=file_bytes, media_type=media_type)
    except Exception as e:
        logger.error(f"EditorJS export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/xem-truoc-latex")
async def preview_latex_source(req: EditorJSCompileRequest):
    """Trả về mã LaTeX được sinh ra từ EditorJS blocks (dùng để debug)."""
    latex = EditorJSEngine.to_latex(
        content=req.content,
        title=req.title,
        author=req.author,
        font_size=req.font_size,
        paper_size=req.paper_size,
    )
    return {"latex": latex, "blocks_count": len(req.content.blocks)}
