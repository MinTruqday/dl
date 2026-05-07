from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import json
from src.agents.router_agent import router_agent_app

router = APIRouter()

class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = "guest"
    document_id: Optional[str] = None
    useWeb: bool = False
    useSmart: bool = False
    image_data: Optional[str] = None
    file_data: Optional[str] = None

@router.post("/chat")
async def chat_endpoint(req: ChatRequest):
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
    config = {"configurable": {"thread_id": f"{req.user_id}_{req.document_id or 'global'}"}}
    result = await router_agent_app.ainvoke(initial_state, config=config)
    return {
        "answer": result.get("final_answer", "Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi."),
        "route": result.get("route", "unknown")
    }

@router.post("/stream")
async def stream_endpoint(req: ChatRequest):
    async def response_generator():
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
        config = {"configurable": {"thread_id": f"{req.user_id}_{req.document_id or 'global'}"}}
        async for event in router_agent_app.astream_events(initial_state, config=config, version="v2"):
            kind = event["event"]
            if kind == "on_node_start":
                yield f"event: status\ndata: {json.dumps({'node': event['name']})}\n\n"
            elif kind == "on_chat_model_stream":
                tags = event.get("tags", [])
                if "final_generator" in tags:
                    content = event["data"]["chunk"].content
                    if content:
                        yield f"event: message\ndata: {json.dumps({'chunk': content})}\n\n"
        yield "event: done\ndata: [DONE]\n\n"
        
    return StreamingResponse(response_generator(), media_type="text/event-stream")
