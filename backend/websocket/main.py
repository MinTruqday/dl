from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from src.api.chat import router as chat_router
from src.api.editor import router as editor_router
from core.database import init_db, close_db

app = FastAPI(title="DocLib WebSocket Gateway")

allowed_origins = [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

app.include_router(chat_router)
app.include_router(editor_router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "websocket"}
