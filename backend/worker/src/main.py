import os
import redis.asyncio as redis
from core.config import settings
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from src.tasks import compile_document_tectonic

app = FastAPI(title="Background Task Service", version=settings.VERSION)
redis_client = redis.from_url(settings.REDIS_URI, decode_responses=True)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=503,
        content={"detail": "Service is experiencing internal technical difficulties please attempt your request again later"}
    )

@app.get("/health")
async def check_health():
    await redis_client.ping()
    return {"status": "Background processing service is operating normally and ready to accept incoming requests"}

@app.post("/documents/compile")
def compile_document(payload: dict):
    doc_id = payload.get("document_id")
    if not doc_id:
        raise HTTPException(
            status_code=400,
            detail="Valid document identifier must be provided in request payload to proceed with compilation"
        )

    task = compile_document_tectonic.delay(doc_id, payload.get("tex_content", ""))
    return {
        "message": "Document successfully added to background processing queue for tectonic compilation",
        "task_id": task.id
    }