import httpx
from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import Response
from loguru import logger
from src.schemas.latex_schema import CompileRequest
from src.services.latex_engine_service import LatexEngine

router = APIRouter()


@router.post("/compile")
async def compile_latex(req: CompileRequest):
    try:
        pdf_bytes = await LatexEngine.compile_to_pdf(req.content)
        return Response(content=pdf_bytes, media_type="application/pdf")
    except Exception:
        logger.error("The system encountered an unexpected error while attempting to compile the formatted typesetting document")
        raise HTTPException(status_code=500, detail="The typesetting compilation process encountered structural errors and could not generate the final document due to invalid syntax or unrecognized commands")


@router.post("/export/{format}")
async def export_document(format: str, req: CompileRequest):
    if format not in ["docx", "html"]:
        raise HTTPException(status_code=400, detail="The requested export format is not currently supported by the conversion system")

    try:
        file_bytes = await LatexEngine.export_to_format(req.content, format)

        media_type = (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
        if format == "html":
            media_type = "text/html"

        return Response(content=file_bytes, media_type=media_type)
    except Exception:
        logger.error("The system encountered an unexpected error while attempting to export the document to the requested format")
        raise HTTPException(status_code=500, detail="The document export process could not be completed due to an internal processing interruption")


@router.post("/format")
async def format_latex(req: CompileRequest):
    return LatexEngine.format_latex(req.content)


@router.post("/export-zip")
async def export_project_zip(req: CompileRequest):
    zip_bytes = LatexEngine.export_project_zip(req.content)
    return Response(content=zip_bytes, media_type="application/x-zip-compressed")