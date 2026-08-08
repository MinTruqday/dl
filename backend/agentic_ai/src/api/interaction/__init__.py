from fastapi import APIRouter
from src.core.logging_route import LoggingRoute

from src.api.interaction.evaluator import router as evaluator_router
from src.api.interaction.executor import router as executor_router
from src.api.interaction.stream import router as stream_router

router = APIRouter(route_class=LoggingRoute, prefix="/tro-chuyen")

router.include_router(evaluator_router)
router.include_router(stream_router)
router.include_router(executor_router)

__all__ = ["router"]
