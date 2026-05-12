from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from typing import Optional
import json
from langchain_core.messages import HumanMessage
from src.agents.router_agent import router_agent_app, router_llm
from src.agents.core_rag import rag_agent_app
from src.agents.action_agent import action_agent_app, auth_token_var
from loguru import logger
from src.models.chat import ChatRequest

router = APIRouter()

@router.post("/tro-chuyen")
async def chat_endpoint(req: ChatRequest, request: Request):
    token = request.headers.get("Authorization")
    if token:
        bearer_token = token.replace("Bearer ", "")
        auth_token_var.set(bearer_token)

    try:
        route_result = await router_agent_app.ainvoke({"question": req.query, "route": ""})
        route = route_result.get("route", "rag")
    except Exception as e:
        logger.error(f"Routing error in /chat: {e}")
        route = "rag"

    config = {"configurable": {"thread_id": f"{req.user_id}_{req.document_id or 'global'}"}}
    answer = "Xin lỗi, tôi gặp sự cố khi xử lý câu hỏi."

    try:
        if route == "action":
            messages = [HumanMessage(content=f"Truy vấn từ ID người dùng <{req.user_id}>: {req.query}")]
            res = await action_agent_app.ainvoke({"messages": messages}, config=config)
            answer = res["messages"][-1].content
        elif route == "chat":
            tagged_llm = router_llm.with_config({"tags": ["final_generator"]})
            prompt = f"Bạn là trợ lý ảo của DocLib. Trả lời người dùng ngắn gọn.\nUser: {req.query}"
            res = await tagged_llm.ainvoke(prompt, config=config)
            answer = res.content.strip()
        else:
            initial_rag_state = {
                "question": req.query,
                "chat_history": [],
                "generation": "",
                "documents": [],
                "retry_count": 0,
                "hallucination_pass": "yes",
                "use_web": req.useWeb,
                "use_smart": req.useSmart,
                "user_id": req.user_id,
                "document_id": req.document_id,
                "image_data": req.image_data,
                "file_data": req.file_data,
                "current_source": "db",
                "route": "rag"
            }
            res = await rag_agent_app.ainvoke(initial_rag_state, config=config)
            answer = res.get("generation", "Tôi không tìm thấy thông tin liên quan trong tài liệu")
    except Exception as e:
        logger.error(f"Execution error in /chat: {e}")

    return {
        "answer": answer,
        "route": route
    }

@router.post("/luong-du-lieu")
async def stream_endpoint(req: ChatRequest, request: Request):
    token = request.headers.get("Authorization")
    bearer_token = token.replace("Bearer ", "") if token else None

    async def response_generator():
        if bearer_token:
            auth_token_var.set(bearer_token)

        try:
            route_result = await router_agent_app.ainvoke({"question": req.query, "route": ""})
            route = route_result.get("route", "rag")
        except Exception as e:
            logger.error(f"Routing error in /stream: {e}")
            route = "rag"

        config = {"configurable": {"thread_id": f"{req.user_id}_{req.document_id or 'global'}"}}

        try:
            if route == "action":
                messages = [HumanMessage(content=f"Truy vấn từ ID người dùng <{req.user_id}>: {req.query}")]
                async for event in action_agent_app.astream_events({"messages": messages}, config=config, version="v2"):
                    kind = event["event"]
                    if kind == "on_chat_model_stream":
                        content = event["data"]["chunk"].content
                        if content and not isinstance(content, list):
                            yield f"event: message\ndata: {json.dumps({'chunk': content})}\n\n"
            elif route == "chat":
                tagged_llm = router_llm.with_config({"tags": ["final_generator"]})
                prompt = f"Bạn là trợ lý ảo của DocLib. Trả lời người dùng ngắn gọn.\nUser: {req.query}"
                async for event in tagged_llm.astream_events(prompt, config=config, version="v2"):
                    kind = event["event"]
                    if kind == "on_chat_model_stream":
                        tags = event.get("tags", [])
                        if "final_generator" in tags:
                            content = event["data"]["chunk"].content
                            if content and not isinstance(content, list):
                                yield f"event: message\ndata: {json.dumps({'chunk': content})}\n\n"
            else:
                initial_rag_state = {
                    "question": req.query,
                    "chat_history": [],
                    "generation": "",
                    "documents": [],
                    "retry_count": 0,
                    "hallucination_pass": "yes",
                    "use_web": req.useWeb,
                    "use_smart": req.useSmart,
                    "user_id": req.user_id,
                    "document_id": req.document_id,
                    "image_data": req.image_data,
                    "file_data": req.file_data,
                    "current_source": "db",
                    "route": "rag"
                }
                async for event in rag_agent_app.astream_events(initial_rag_state, config=config, version="v2"):
                    kind = event["event"]
                    if kind == "on_node_start":
                        yield f"event: status\ndata: {json.dumps({'node': event['name']})}\n\n"
                    elif kind == "on_chat_model_stream":
                        tags = event.get("tags", [])
                        if "final_generator" in tags:
                            content = event["data"]["chunk"].content
                            if content and not isinstance(content, list):
                                yield f"event: message\ndata: {json.dumps({'chunk': content})}\n\n"
        except Exception as e:
            logger.error(f"Stream execution error: {e}")
            yield f"event: message\ndata: {json.dumps({'chunk': 'Lỗi hệ thống khi sinh câu trả lời'})}\n\n"
            
        yield "event: done\ndata: [DONE]\n\n"
        
    return StreamingResponse(response_generator(), media_type="text/event-stream")
