from fastapi import APIRouter
from src.core.logging_route import LoggingRoute

from src.api.interaction.evaluator import router as evaluator_router
from src.api.interaction.executor import require_mode_tier, router as executor_router
from src.api.interaction.stream import router as stream_router

router = APIRouter(route_class=LoggingRoute)

router.include_router(evaluator_router, prefix="/tro-chuyen")
router.include_router(stream_router, prefix="/tro-chuyen")
router.include_router(executor_router, prefix="/tro-chuyen")

__all__ = ["router", "require_mode_tier"]
