from fastapi import APIRouter

from .api.bulk import router as bulk_router
from .api.internal_admin import router as internal_admin_router
from .api.internal_jobs import router as internal_jobs_router
from .api.jobs import router as jobs_router
from .api.notifications import router as notifications_router
from .api.operations import router as operations_router


router = APIRouter()
router.include_router(bulk_router)
router.include_router(internal_jobs_router)
router.include_router(internal_admin_router)
router.include_router(jobs_router)
router.include_router(notifications_router)
router.include_router(operations_router)
