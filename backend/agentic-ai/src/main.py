from fastapi import FastAPI
from loguru import logger
from src.api.inference import router as inference_router
from src.api.chat import router as chat_router
from src.api.ingest import router as ingest_router
from src.api.feedback import router as feedback_router
from src.api.finetune import router as finetune_router

app = FastAPI(title="DocLib Agentic AI")

app.include_router(inference_router, prefix="/inference", tags=["Inference"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(ingest_router, tags=["Ingestion"])
app.include_router(feedback_router, tags=["Feedback"])
app.include_router(finetune_router, tags=["Fine-tuning"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    from src.store.vector_store import vector_store
    try:
        await vector_store.ensure_collection()
        logger.info("Qdrant collection ensured successfully.")
    except Exception as e:
        logger.error(f"Failed to ensure Qdrant collection: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
