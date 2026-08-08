from fastapi import APIRouter
from src.core.logging_route import LoggingRoute

from src.api.document.internal import router as internal_router
from src.api.document.tag import router as tag_router
from src.api.document.hierarchy import router as hierarchy_router
from src.api.document.metadata import router as metadata_router
from src.api.document.bulk import router as bulk_router
from src.api.document.crud import router as crud_router

router = APIRouter(route_class=LoggingRoute)

router.include_router(internal_router, prefix="/tai-lieu")
router.include_router(tag_router, prefix="/tai-lieu")
router.include_router(hierarchy_router, prefix="/tai-lieu")
router.include_router(metadata_router, prefix="/tai-lieu")
router.include_router(bulk_router, prefix="/tai-lieu")
router.include_router(crud_router, prefix="/tai-lieu")

__all__ = ["router"]
