import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import init_db, close_db

from src.api.document import router as document_router
from src.api.review import router as review_router
from src.api.version import router as version_router
from src.api.reading import router as reading_router
from src.api.bookmark import router as bookmark_router
from src.api.library import router as library_router
from src.api.upload import router as upload_router
from src.api.discovery import router as discovery_router
from src.api.export import router as export_router
from src.api.collaboration import router as collaboration_router
from src.api.publication import router as publication_router
from src.api.storage import router as storage_router
from src.api.highlight import router as highlight_router
from src.api.draft import router as draft_router
from src.api.pin import router as pin_router

app = FastAPI(title="DocLib Content")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS.split(",") if settings.CORS_ALLOWED_ORIGINS else ["*"],
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
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "content"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8450, reload=True)
