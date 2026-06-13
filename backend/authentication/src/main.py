import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.authentication import router as auth_router
from src.api.passkey import router as passkey_router

app = FastAPI(title="DocLib Authentication", version=settings.VERSION)

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

app.include_router(auth_router)
app.include_router(passkey_router)


@app.on_event("startup")
async def startup_event():
    logger.info("Đã khởi tạo hệ thống bảo mật DocLib")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "authentication"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8500, reload=True)
