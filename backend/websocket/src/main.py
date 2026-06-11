import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.router import editor_ws, message_ws
from core.config import settings
from src.core.database import db_client

app = FastAPI(title="DocLib WebSocket")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(editor_ws.router, prefix="/soan-thao")
app.include_router(message_ws.router, prefix="/tin-nhan")

@app.on_event("startup")
async def startup_event():
    await db_client.connect()

@app.on_event("shutdown")
async def shutdown_event():
    await db_client.disconnect()

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "websocket"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8200, reload=True)
