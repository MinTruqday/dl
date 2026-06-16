from contextlib import asynccontextmanager
import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.router.bookmarks import router as bookmark_router
from src.router.collaboration import router as collaboration_router
from src.router.discovery import router as discovery_router
from src.router.documents import router as document_router
from src.router.drafts import router as draft_router
from src.router.exports import router as export_router
from src.router.highlights import router as highlight_router
from src.router.library import router as library_router
from src.router.pins import router as pin_router
from src.router.publication import router as publication_router
from src.router.reading import router as reading_router
from src.router.reviews import router as review_router
from src.router.storage import router as storage_router
from src.router.uploads import router as upload_router
from src.router.versions import router as version_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Primary content management service initialized successfully and ready to process incoming requests")
    await init_db()
    yield
    await close_db()

app = FastAPI(title="DocLib Content", version=settings.VERSION, lifespan=lifespan)

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

@app.get("/health")
async def health_check():
    return {"status": "Content management service is currently operating normally and functioning as expected without internal issues"}