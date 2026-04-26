from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from loguru import logger
from src.agents.router_agent import router_agent_app
from src.ingestion.pipeline import ingestion_pipeline
from src.store.vector_store import vector_store

app = FastAPI(title="DocLib Agentic RAG API")

class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = "guest"
    document_id: Optional[str] = None
    useWeb: bool = False
    useSmart: bool = False
    image_data: Optional[str] = None
    file_data: Optional[str] = None

class IngestRequest(BaseModel):
    document_id: str

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    logger.info(f"Chat request for document_id: {req.document_id}")
    
    initial_state = {
        "question": req.query,
        "user_id": req.user_id,
        "document_id": req.document_id,
        "route": "",
        "final_answer": "",
        "use_web": req.useWeb,
        "use_smart": req.useSmart,
        "image_data": req.image_data,
        "file_data": req.file_data
    }
    
    try:
        config = {"configurable": {"thread_id": f"{req.user_id}_{req.document_id or 'global'}"}}
        result = router_agent_app.invoke(initial_state, config=config)
        return {
            "answer": result.get("final_answer", "Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi."),
            "route": result.get("route", "unknown")
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ingest")
async def ingest_endpoint(req: IngestRequest):
    logger.info(f"Ingest request for document_id: {req.document_id}")
    try:
        result = await ingestion_pipeline.ingest_document(req.document_id)
        return result
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info(f"Delete request for document_id: {document_id}")
    try:
        vector_store.delete_by_document(document_id)
        return {"status": "success", "message": f"Deleted vectors for document {document_id}"}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
