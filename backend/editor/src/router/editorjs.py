from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from loguru import logger
from src.schemas.editorjs import CompileRequest
from src.services.editorjs_engine import EditorJSEngine

router = APIRouter()

@router.post("/compile")
async def compile_editorjs(req: CompileRequest):
    try:
        pdf_bytes = await EditorJSEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception:
        logger.error("System encountered unexpected error attempting to compile visual document content")
        raise HTTPException(
            status_code=500, 
            detail="Document compilation process failed due to an internal system processing interruption"
        )