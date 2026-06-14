import uvicorn
from core.config import settings
from core.database import close_db, init_db
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.router.message_router import router as message_router

app = FastAPI(title="DocLib Contact", version=settings.VERSION)

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

app.include_router(message_router)


@app.on_event("startup")
async def startup_event():
    logger.info("DocLib Contact initialized successfully")
    await init_db()


@app.on_event("shutdown")
async def shutdown_event():
    await close_db()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "contact"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8100, reload=True)
