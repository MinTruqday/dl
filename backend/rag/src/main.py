from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
from loguru import logger

from src.api.retrieval import router as retrieval_router
from src.api.embedding import router as embedding_router
from src.api.ingestion import router as ingestion_router
from src.api.cache import router as cache_router

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import close_db, database, init_db
from src.core.infrastructure.redis import redis_client
from src.core.metrics import PrometheusMiddleware, metrics_endpoint
from src.store.vector import vector_store
from src.store.bm25 import bm25_store
from src.services.embedding import embedder
from src.services.retrieval import retriever


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await redis_client.init_redis()
    embedding = await embedder.initialize()
    if len(embedding) != embedder._dimensions:
        raise RuntimeError("Embedding model dimension does not match the vector index")
    await vector_store.ensure_collection()
    await bm25_store.initialize(await vector_store.scroll_all())
    await retriever.initialize()
    logger.info("RAG Knowledge service initialized and ready")
    try:
        yield
    finally:
        await redis_client.close_redis()
        await close_db()


app = FastAPI(title="DocLib RAG", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(PrometheusMiddleware, service_name="rag")
app.add_route("/metrics", metrics_endpoint("rag"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
        if settings.CORS_ALLOWED_ORIGINS
        else ["*"]
    ),
    allow_credentials=bool(settings.CORS_ALLOWED_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(retrieval_router, prefix="/rag")
app.include_router(embedding_router, prefix="/rag/embedding")
app.include_router(ingestion_router, prefix="/rag")
app.include_router(cache_router, prefix="/rag/cache")


@app.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "healthy", "service": "rag"}


@app.get("/ready", include_in_schema=False)
async def readiness_check():
    checks = {}
    try:
        if database.mongodb is not None:
            await database.mongodb.command("ping")
            checks["mongodb"] = "ready"
        else:
            checks["mongodb"] = "unavailable"
    except Exception:
        checks["mongodb"] = "unavailable"
    try:
        checks["redis"] = (
            "ready" if redis_client.client and await redis_client.client.ping() else "unavailable"
        )
    except Exception:
        checks["redis"] = "unavailable"
    try:
        collections = await vector_store.client.get_collections()
        checks["qdrant"] = (
            "ready"
            if any(item.name == vector_store.collection_name for item in collections.collections)
            else "unavailable"
        )
    except Exception:
        checks["qdrant"] = "unavailable"
    checks["embedding"] = "ready" if embedder._model is not None else "unavailable"
    checks["reranker"] = "ready" if retriever._reranker is not None else "unavailable"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.CONTENT_URL}/ready")
        checks["content"] = "ready" if response.status_code == 200 else "unavailable"
    except Exception:
        checks["content"] = "unavailable"
    ready = all(value == "ready" for value in checks.values())
    return JSONResponse(
        status_code=200 if ready else 503,
        content={"status": "ready" if ready else "degraded", "checks": checks, "service": "rag"},
    )
