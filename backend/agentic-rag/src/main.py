from fastapi import FastAPI
from loguru import logger
from src.router.inference import router as inference_router
from src.router.chat import router as chat_router
from src.router.ingest import router as ingest_router
from src.router.feedback import router as feedback_router

app = FastAPI(title="DocLib Agentic RAG")

app.include_router(inference_router, prefix="/inference", tags=["Inference"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(ingest_router, tags=["Ingestion"])
app.include_router(feedback_router, tags=["Feedback"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
