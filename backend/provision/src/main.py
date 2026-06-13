import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from core.database import init_db, close_db
from src.api.user import router as user_router
from src.api.audit import router as audit_router
from src.api.telemetry import router as telemetry_router
from src.api.operation import router as operation_router
from src.api.quota import router as quota_router

app = FastAPI(title="DocLib Provision", version=settings.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS.split(",") if settings.CORS_ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(audit_router)
app.include_router(telemetry_router)
app.include_router(operation_router)
app.include_router(quota_router)

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

@app.get("/kiem-tra-suc-khoe")
async def health_check():
    return {"status": "ok", "service": "provision"}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8050, reload=True)
