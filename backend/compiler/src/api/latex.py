from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import Response
from src.schemas.latex import CompileRequest
from src.services.latex_engine import LatexEngine
from loguru import logger
import httpx

router = APIRouter()

@router.post("/bien-dich")
async def compile_latex(req: CompileRequest):
    try:
        pdf_bytes = await LatexEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        logger.error(f"Compile error: {e}")
        if isinstance(e.args[0], dict):
            raise HTTPException(status_code=400, detail=e.args[0])
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/xuat/{format}")
async def export_document(format: str, req: CompileRequest):
    if format not in ["docx", "html"]:
        raise HTTPException(status_code=400, detail="Định dạng không hỗ trợ.")
    
    try:
        file_bytes = await LatexEngine.export_to_format(req.content, format)
        
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        if format == "html":
            media_type = "text/html"
            
        return Response(content=file_bytes, media_type=media_type)
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dinh-dang")
async def format_latex(req: CompileRequest):
    return LatexEngine.format_latex(req.content)

@router.post("/xuat-zip")
async def export_project_zip(req: CompileRequest):
    zip_bytes = LatexEngine.export_project_zip(req.content)
    return Response(content=zip_bytes, media_type="application/x-zip-compressed")

