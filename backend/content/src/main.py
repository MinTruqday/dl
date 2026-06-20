import uvicorn
from core.config import settings
from loguru import logger
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.router.bookmark_router import router as bookmark_router
from src.router.collaboration_router import router as collaboration_router
from src.router.discovery_router import router as discovery_router
from src.router.document_router import router as document_router
from src.router.draft_router import router as draft_router
from src.router.export_router import router as export_router
from src.router.highlight_router import router as highlight_router
from src.router.library_router import router as library_router
from src.router.pin_router import router as pin_router
from src.router.publication_router import router as publication_router
from src.router.reading_router import router as reading_router
from src.router.review_router import router as review_router
from src.router.storage_router import router as storage_router
from src.router.upload_router import router as upload_router
from src.router.version_router import router as version_router

app = FastAPI(title="DocLib Content", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        settings.CORS_ALLOWED_ORIGINS.split(",")
        if settings.CORS_ALLOWED_ORIGINS
        else ["*"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(document_router)
app.include_router(review_router)
app.include_router(version_router)
app.include_router(reading_router)
app.include_router(bookmark_router)
app.include_router(library_router)
app.include_router(upload_router)
app.include_router(discovery_router)
app.include_router(export_router)
app.include_router(collaboration_router)
app.include_router(publication_router)
app.include_router(storage_router)
app.include_router(highlight_router)
app.include_router(draft_router)
app.include_router(pin_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Quản lý nội dung đã sẵn sàng")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {"status": "The content management service is currently operating normally and functioning as expected without any internal issues"}