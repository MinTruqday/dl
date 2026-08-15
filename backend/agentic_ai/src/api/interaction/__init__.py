from fastapi import APIRouter

from src.api.interaction.evaluator import router as evaluator_router
from src.api.interaction.executor import router as executor_router
from src.api.interaction.stream import router as stream_router

router = APIRouter()

router.include_router(evaluator_router, prefix="/tro-chuyen")
router.include_router(stream_router, prefix="/tro-chuyen")
router.include_router(executor_router, prefix="/tro-chuyen")

__all__ = ["router"]
