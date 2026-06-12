from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from src.services.editorjs_engine import EditorJSEngine
from loguru import logger

router = APIRouter()

class CompileRequest(BaseModel):
    content: str = Field(...)

@router.post("/bien-dich")
async def compile_editorjs(req: CompileRequest):
    try:
        pdf_bytes = await EditorJSEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception as e:
        logger.error(f"Lỗi biên dịch: {e}")
        raise HTTPException(status_code=500, detail=str(e))
