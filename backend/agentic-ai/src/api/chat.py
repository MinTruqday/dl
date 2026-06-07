import httpx
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json
from loguru import logger
from src.schemas.chat import ChatRequest

from src.workflow.supervisor import supervisor
from src.agents.semantic_router import semantic_router
from src.core.prompt_registry import prompt_registry, PromptType


router = APIRouter()

@router.post("/tro-chuyen")
async def chat_endpoint(req: ChatRequest, request: Request):
    token = request.headers.get("Authorization")
    if token:
        bearer_token = token.replace("Bearer ", "")

        req.token = bearer_token

    try:
        if req.document_ids:
            from src.tools.api_tools import _make_api_request, INTERNAL_API_URL
            for doc_id in req.document_ids:
                try:
                    doc_res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{doc_id}", headers={"Authorization": f"Bearer {req.token}"}, timeout=10)
                    if doc_res.status_code not in [200, 201]:
                        return {"answer": f"Lỗi bảo mật: Bạn không có quyền truy cập vào tài liệu {doc_id} hoặc tài liệu không tồn tại.", "route": "error"}
                except Exception as e:
                    logger.error(f"Error checking document access for {doc_id}: {e}")
                    return {"answer": f"Lỗi: Không thể xác thực quyền truy cập tài liệu {doc_id} lúc này.", "route": "error"}
                
        route_data = await semantic_router.execute(req.query)
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
                
                text_prompt = prompt_registry.get(PromptType.CHAT_ASSISTANT).format(query=req.query)
                if req.image_data:
                    content = [
                        {"type": "text", "text": text_prompt},
                        {"type": "image_url", "image_url": {"url": req.image_data}}
                    ]
                else:
                    content = text_prompt
                    
                res = await chat_llm.ainvoke([HumanMessage(content=content)])
                final_answer = res.content
        else:
            async for event in supervisor.execute_plan(req):
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

            req.token = bearer_token

        from src.memory.manager import memory_manager
        
        try:
            if req.document_ids:
                from src.tools.api_tools import _make_api_request, INTERNAL_API_URL
                for doc_id in req.document_ids:
                    try:
                        doc_res = await _make_api_request("GET", f"{INTERNAL_API_URL}/tai-lieu/{doc_id}", headers={"Authorization": f"Bearer {req.token}"}, timeout=10)
                        if doc_res.status_code not in [200, 201]:
                            yield f"event: message\ndata: {json.dumps({'chunk': f'Lỗi bảo mật: Bạn không có quyền truy cập vào tài liệu {doc_id}.'})}\n\n"
                            return
                    except Exception as e:
                        logger.error(f"Error checking document access for {doc_id}: {e}")
                        yield f"event: message\ndata: {json.dumps({'chunk': f'Lỗi: Không thể xác thực quyền truy cập tài liệu {doc_id}.'})}\n\n"
                        return
                    
            if req.session_id:
                history = await memory_manager.get_short_term(req.session_id)
                if history:
                    req.conversation_history = history
            
            route_data = await semantic_router.execute(req.query)
            route = route_data["route"]
            final_answer = ""
            
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
                    
                    text_prompt = prompt_registry.get(PromptType.CHAT_ASSISTANT).format(query=req.query)
                    if req.image_data:
                        content = [
                            {"type": "text", "text": text_prompt},
                            {"type": "image_url", "image_url": {"url": req.image_data}}
                        ]
                    else:
                        content = text_prompt
                        
                    async for chunk in chat_llm.astream([HumanMessage(content=content)]):
                        if chunk.content:
                            final_answer += chunk.content
                            yield f"event: message\ndata: {json.dumps({'chunk': chunk.content})}\n\n"
                            
                if req.session_id:
                    await memory_manager.save_short_term(req.session_id, {"role": "user", "content": req.query})
                    await memory_manager.save_short_term(req.session_id, {"role": "assistant", "content": final_answer})
            else:
                import asyncio

                heartbeat_queue: asyncio.Queue = asyncio.Queue()

                async def heartbeat_sender():
                    while True:
                        await asyncio.sleep(10)
                        await heartbeat_queue.put({"type": "heartbeat"})

                hb_task = asyncio.create_task(heartbeat_sender())

                async def drain_supervisor():
                    async for event in supervisor.execute_plan(req):
                        await heartbeat_queue.put(event)
                    await heartbeat_queue.put({"type": "__done__"})

                exec_task = asyncio.create_task(drain_supervisor())

                try:
                    while True:
                        event = await heartbeat_queue.get()
                        event_type = event["type"]

                        if event_type == "__done__":
                            break
                        elif event_type == "heartbeat":
                            yield f"event: heartbeat\ndata: {{}}\n\n"
                        elif event_type == "status":
                            yield f"event: status\ndata: {json.dumps({'node': event['node']})}\n\n"
                        elif event_type == "plan":
                            yield f"event: plan\ndata: {json.dumps({'steps': event['steps']})}\n\n"
                        elif event_type == "tool_result":
                            yield f"event: tool\ndata: {json.dumps({'agent': event['agent'], 'result': event.get('content', 'Hoàn thành')})}\n\n"
                        elif event_type == "message":
                            final_answer += event['chunk']
                            yield f"event: message\ndata: {json.dumps({'chunk': event['chunk']})}\n\n"
                        elif event_type == "error":
                            yield f"event: message\ndata: {json.dumps({'chunk': event['message']})}\n\n"
                finally:
                    hb_task.cancel()
                    exec_task.cancel()

                if req.session_id and final_answer:
                    await memory_manager.save_short_term(req.session_id, {"role": "user", "content": req.query})
                    await memory_manager.save_short_term(req.session_id, {"role": "assistant", "content": final_answer})
                    
        except Exception as e:
            logger.exception(f"Stream execution error: {e}")
            yield f"event: message\ndata: {json.dumps({'chunk': 'Hệ thống đang gặp sự cố, vui lòng thử lại sau.'})}\n\n"
            
        yield "event: done\ndata: [DONE]\n\n"
        
    return StreamingResponse(response_generator(), media_type="text/event-stream")
