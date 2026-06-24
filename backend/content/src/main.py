import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from src.api.bookmark import router as bookmark
from src.api.collaboration import router as collaboration
from src.api.discovery import router as discovery
from src.api.document import router as document
from src.api.draft import router as draft
# from src.api.export import router as export
from src.api.highlight import router as highlight
from src.api.library import router as library
from src.api.pin import router as pin
from src.api.publication import router as publication
from src.api.reading import router as reading
from src.api.discovery import router as review

from src.api.version import router as version

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, init_db

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

app.include_router(document)
app.include_router(review)
app.include_router(version)
app.include_router(reading)
app.include_router(bookmark)
app.include_router(library)

app.include_router(discovery)
# app.include_router(export)
app.include_router(collaboration)
app.include_router(publication)

app.include_router(highlight)
app.include_router(draft)
app.include_router(pin)


@app.on_event("startup")
async def startup_event():
    logger.info("Quản lý nội dung đã sẵn sàng")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {
        "status": "The content management service is currently operating normally and functioning as expected without any internal issues"
    }
