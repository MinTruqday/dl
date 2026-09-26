from fastapi import APIRouter

from src.api.requirement_analysis import router as analysis_router
from src.api.requirement_documents import router as documents_router
from src.api.requirement_imports import router as imports_router
from src.api.requirement_records import router as records_router


router = APIRouter()
router.include_router(records_router)
router.include_router(analysis_router)
router.include_router(documents_router)
router.include_router(imports_router)
