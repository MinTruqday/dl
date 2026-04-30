from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
import os
from loguru import logger
from src.agents.router_agent import router_agent_app
from src.ingestion.pipeline import ingestion_pipeline
from src.store.vector_store import vector_store
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient
from src.routers.inference import router as inference_router

app = FastAPI()
app.include_router(inference_router, prefix="/inference")

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

class FeedbackRequest(BaseModel):
    session_id: str
    message_id: str
    user_id: Optional[str] = "guest"
    vote_type: str = Field(..., description="Must be 'upvote', 'downvote', or 'hallucination_report'")
    comment: Optional[str] = ""

@app.post("/chat")
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
        result = await router_agent_app.ainvoke(initial_state, config=config)
        return {
            "answer": result.get("final_answer", "Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi."),
            "route": result.get("route", "unknown")
        }
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail="Hệ thống đang bận xử lý yêu cầu, vui lòng thử lại sau.")

@app.post("/stream")
async def stream_endpoint(req: ChatRequest):
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
    
    async def response_generator():
        try:
            config = {"configurable": {"thread_id": f"{req.user_id}_{req.document_id or 'global'}"}}
            async for chunk in router_agent_app.astream(initial_state, config=config, stream_mode="updates"):
                import json
                for node_name, node_output in chunk.items():
                    yield f"event: status\ndata: {json.dumps({'node': node_name})}\n\n"
                    msg = node_output.get("final_answer", "")
                    if msg:
                        yield f"event: message\ndata: {json.dumps({'chunk': msg})}\n\n"
            
            yield "event: done\ndata: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    from fastapi.responses import StreamingResponse
    return StreamingResponse(response_generator(), media_type="text/event-stream")

@app.post("/ingest")
async def ingest_endpoint(req: IngestRequest):
    logger.info(f"Ingest request for document_id: {req.document_id}")
    try:
        result = await ingestion_pipeline.ingest_document(req.document_id)
        return result
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail="Gặp sự cố khi đồng bộ tài liệu, vui lòng thử lại sau.")

@app.delete("/documents/{document_id}")
async def delete_document_endpoint(document_id: str):
    logger.info(f"Delete request for document_id: {document_id}")
    try:
        vector_store.delete_by_document(document_id)
        return {"status": "success", "message": f"Deleted vectors for document {document_id}"}
    except Exception as e:
        logger.error(f"Delete error: {e}")
        raise HTTPException(status_code=500, detail="Không thể xóa dữ liệu vào lúc này.")

@app.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    if req.vote_type not in ["upvote", "downvote", "hallucination_report"]:
        raise HTTPException(status_code=400, detail="Invalid vote_type. Must be 'upvote', 'downvote', or 'hallucination_report'")
        
    try:
        from src.core.config import settings
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client.doclib
        
        feedback_doc = {
            "session_id": req.session_id,
            "message_id": req.message_id,
            "user_id": req.user_id,
            "vote_type": req.vote_type,
            "comment": req.comment,
            "created_at": datetime.utcnow()
        }
        
        await db.rag_feedback.insert_one(feedback_doc)
        client.close()
        logger.info(f"Feedback saved for message {req.message_id} ({req.vote_type})")
        
        return {"status": "success", "message": "Cảm ơn bạn đã đóng góp ý kiến."}
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        raise HTTPException(status_code=500, detail="Hệ thống đang bảo trì dữ liệu, vui lòng thử lại sau.")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
