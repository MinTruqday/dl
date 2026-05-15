from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json
from loguru import logger
from src.models.chat import ChatRequest
from src.agents.action_agent import auth_token_var
from src.agents.coordinator import coordinator

router = APIRouter()

@router.post("/tro-chuyen")
async def chat_endpoint(req: ChatRequest, request: Request):
    token = request.headers.get("Authorization")
    if token:
        bearer_token = token.replace("Bearer ", "")
        auth_token_var.set(bearer_token)

    try:
        final_answer = ""
        async for event in coordinator.execute_plan(req.query, req.context if hasattr(req, 'context') else "", req.user_id):
            if event["type"] == "message":
                final_answer += event.get("chunk", "")
                
        return {
            "answer": final_answer or "Hệ thống đang bảo trì dữ liệu.",
            "route": "agentic_ai"
        }
    except Exception as e:
        logger.error(f"Execution error in /chat: {e}")
        return {"answer": "Xin lỗi, hệ thống gặp sự cố.", "route": "error"}

@router.post("/luong-du-lieu")
async def stream_endpoint(req: ChatRequest, request: Request):
    token = request.headers.get("Authorization")
    bearer_token = token.replace("Bearer ", "") if token else None

    async def response_generator():
        if bearer_token:
            auth_token_var.set(bearer_token)

        try:
            async for event in coordinator.execute_plan(req.query, req.context if hasattr(req, 'context') else "", req.user_id):
                event_type = event["type"]
                
                if event_type == "status":
                    yield f"event: status\ndata: {json.dumps({'node': event['node']})}\n\n"
                elif event_type == "plan":
                    yield f"event: plan\ndata: {json.dumps({'steps': event['steps']})}\n\n"
                elif event_type == "tool_result":
                    yield f"event: tool\ndata: {json.dumps({'agent': event['agent'], 'result': event['content']})}\n\n"
                elif event_type == "message":
                    yield f"event: message\ndata: {json.dumps({'chunk': event['chunk']})}\n\n"
                elif event_type == "error":
                    yield f"event: message\ndata: {json.dumps({'chunk': event['message']})}\n\n"
                    
        except Exception as e:
            logger.error(f"Stream execution error: {e}")
            yield f"event: message\ndata: {json.dumps({'chunk': 'Lỗi hệ thống khi điều phối Agents'})}\n\n"
            
        yield "event: done\ndata: [DONE]\n\n"
        
    return StreamingResponse(response_generator(), media_type="text/event-stream")
