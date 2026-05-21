import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json
from loguru import logger
from src.models.chat import ChatRequest
from src.agents.action import auth_token_var
from src.core.coordinator import coordinator
from src.agents.router import router_agent

router = APIRouter()

@router.post("/tro-chuyen")
async def chat_endpoint(req: ChatRequest, request: Request):
    token = request.headers.get("Authorization")
    if token:
        bearer_token = token.replace("Bearer ", "")
        auth_token_var.set(bearer_token)

    try:
        route_data = await router_agent.execute(req.query)
        route = route_data["route"]
        final_answer = ""
        
        if route == "chat":
            final_answer = route_data.get("answer", "")
            if not final_answer:
                from src.utils.hf import HFInferenceChat
                from huggingface_hub import AsyncInferenceClient
                from src.core.config import settings
                from langchain_core.messages import HumanMessage
                
                llama_client = AsyncInferenceClient(model=settings.LLAMA_MODEL, token=settings.HF_TOKEN)
                chat_llm = HFInferenceChat(client=llama_client, model=settings.LLAMA_MODEL)
                res = await chat_llm.ainvoke([HumanMessage(content=f"Bạn là trợ lý ảo DocLib. Hãy trả lời ngắn gọn, thân thiện bằng tiếng Việt. Câu hỏi: {req.query}")])
                final_answer = res.content
        else:
            async for event in coordinator.execute_plan(req):
                if event["type"] == "message":
                    final_answer += event.get("chunk", "")
                
        return {
            "answer": final_answer or "Hệ thống đang gặp sự cố, vui lòng thử lại sau.",
            "route": "agentic_ai"
        }
    except Exception as e:
        logger.error(f"Execution error in /chat: {e}")
        return {"answer": "Hệ thống đang gặp sự cố, vui lòng thử lại sau.", "route": "error"}

@router.post("/luong-du-lieu")
async def stream_endpoint(req: ChatRequest, request: Request):
    token = request.headers.get("Authorization")
    bearer_token = token.replace("Bearer ", "") if token else None

    async def response_generator():
        if bearer_token:
            auth_token_var.set(bearer_token)

        try:
            route_data = await router_agent.execute(req.query)
            route = route_data["route"]
            
            if route == "chat":
                yield f"event: status\ndata: {json.dumps({'node': 'Đang phản hồi trực tiếp'})}\n\n"
                
                fast_answer = route_data.get("answer", "")
                if fast_answer:
                    yield f"event: message\ndata: {json.dumps({'chunk': fast_answer})}\n\n"
                else:
                    from src.utils.hf import HFInferenceChat
                    from huggingface_hub import AsyncInferenceClient
                    from src.core.config import settings
                    from langchain_core.messages import HumanMessage
                    
                    llama_client = AsyncInferenceClient(model=settings.LLAMA_MODEL, token=settings.HF_TOKEN)
                    chat_llm = HFInferenceChat(client=llama_client, model=settings.LLAMA_MODEL)
                    
                    res = await chat_llm.ainvoke([HumanMessage(content=f"Bạn là trợ lý ảo DocLib. Hãy trả lời ngắn gọn, thân thiện bằng tiếng Việt. Câu hỏi: {req.query}")])
                    yield f"event: message\ndata: {json.dumps({'chunk': res.content})}\n\n"
            else:
                async for event in coordinator.execute_plan(req):
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
            yield f"event: message\ndata: {json.dumps({'chunk': 'Hệ thống đang gặp sự cố, vui lòng thử lại sau.'})}\n\n"
            
        yield "event: done\ndata: [DONE]\n\n"
        
    return StreamingResponse(response_generator(), media_type="text/event-stream")
