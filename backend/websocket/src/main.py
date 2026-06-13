import uvicorn
from core.config import settings
from core.database import db_client
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api import editor_ws, message_ws

app = FastAPI(title="DocLib WebSocket")

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

app.include_router(editor_ws.router, prefix="/soan-thao")
app.include_router(message_ws.router, prefix="/tin-nhan")


@app.on_event("startup")
async def startup_event():
    from core.database import init_db

    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    from core.database import close_db

    await close_db()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "websocket"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8200, reload=True)
