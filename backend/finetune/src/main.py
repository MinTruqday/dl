from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.routes import router
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


@asynccontextmanager
async def lifespan(_: FastAPI):
    await database.setup_indexes()
    yield
    await database.close()


app = FastAPI(
    title="DocLib Model Training",
    version=settings.VERSION,
    lifespan=lifespan,
)
origins = settings.CORS_ALLOWED_ORIGINS.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials="*" not in origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/ready")
async def ready():
    checks = {}
    try:
        await database.mongodb.command("ping")
        checks["mongodb"] = "ready"
    except Exception:
        checks["mongodb"] = "unavailable"
    ready_state = all(value == "ready" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready_state else 503,
        content={
            "status": "ready" if ready_state else "degraded",
            "checks": checks,
        },
    )
