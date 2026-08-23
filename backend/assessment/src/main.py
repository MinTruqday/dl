from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.authoring import router as authoring_router
from src.api.delivery import router as delivery_router
from src.api.education import router as education_router
from src.api.operations import router as operations_router
from src.core.configuration import settings
from src.core.database import close_database, connect_database, database
from src.core.metrics import PrometheusMiddleware, metrics_endpoint


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_database()
    yield
    await close_database()


app = FastAPI(title="Assessment Core", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="assessment")
app.add_route("/metrics", metrics_endpoint("assessment"))
origins = [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(education_router)
app.include_router(authoring_router)
app.include_router(delivery_router)
app.include_router(operations_router)


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "healthy", "service": "assessment"}


@app.get("/ready", include_in_schema=False)
async def ready():
    try:
        if database.client is None:
            raise RuntimeError
        await database.client.admin.command("ping")
        return {"status": "ready", "service": "assessment"}
    except Exception:
        return JSONResponse(
            status_code=503, content={"status": "not_ready", "service": "assessment"}
        )
