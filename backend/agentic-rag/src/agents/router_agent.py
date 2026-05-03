import os
from typing import Dict, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from loguru import logger
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from src.core.config import settings
from src.agents.core_rag import rag_agent_app
from src.agents.billing_agent import billing_agent_app
from src.agents.workspace_agent import workspace_agent_app

class RouterState(TypedDict):
    question: str
    user_id: str
    document_id: str
    route: str 
    final_answer: str
    use_web: bool
    use_smart: bool
    image_data: str
    file_data: str

llama_model = settings.LLAMA_MODEL
if not llama_model:
    raise ValueError("LLAMA_MODEL is not set")

_hf_endpoint = HuggingFaceEndpoint(
    repo_id=llama_model,
    huggingfacehub_api_token=settings.HF_TOKEN,
    temperature=0.1,
    task="conversational",
    streaming=True
)
router_llm = ChatHuggingFace(llm=_hf_endpoint)

class RouteDecision(BaseModel):
    destination: Literal["rag", "billing", "workspace", "chat"] = Field(description="Luồng AI mà câu hỏi cần được gửi đến")

def route_query(state: RouterState):
    logger.info(f"Routing query: {state['question'][:50]}")
    question = state["question"]
    
    prompt = PromptTemplate(
        template="""Bạn là router chuyên gia của hệ thống DocLib. Bạn phân tích ý định câu hỏi và chuyển hướng đến đúng luồng xử lý.
        
        Quy tắc định tuyến:
        - "rag": Câu hỏi liên quan đến nội dung tài liệu, kiến thức tìm kiếm, giải thích đoạn văn, tóm tắt nội dung.
        - "billing": Câu hỏi liên quan đến tài khoản, thanh toán, ví người dùng, số dư dl, nạp tiền, doanh thu.
        - "workspace": Câu hỏi liên quan đến quản lý thư viện, xóa tài liệu, khôi phục thùng rác, xem thống kê độc giả, quản lý file cá nhân.
        - "multi": Câu hỏi yêu cầu thông tin tổng hợp từ nhiều nguồn (ví dụ: vừa hỏi số dư vừa hỏi tài liệu).
        - "chat": Câu hỏi chào hỏi giao tiếp thông thường.
        
        Câu hỏi: {question}
        Trả lời duy nhất "rag", "billing", "workspace", "multi" hoặc "chat":""",
        input_variables=["question"]
    )
    
    try:
        response = router_llm.invoke(prompt.format(question=question))
        decision = response.content.strip().lower()
    except Exception as e:
        logger.error(f"Router LLM error: {e}")
        decision = "rag"
    
    route = "rag" 
    if "workspace" in decision:
        route = "workspace"
    elif "chat" in decision:
        route = "chat"
    elif "multi" in decision:
        route = "multi"
    elif "billing" in decision:
        route = "billing"
    elif "rag" in decision:
        route = "rag"
    
    logger.info(f"Routing decision: {route.upper()}")
    return {"route": route, "question": question}

async def rag_node(state: RouterState):
    initial_rag_state = {
        "question": state["question"],
        "chat_history": [],
        "generation": "",
        "documents": [],
        "retry_count": 0,
        "hallucination_pass": "yes",
        "use_web": state.get("use_web", False),
        "use_smart": state.get("use_smart", False),
        "user_id": state.get("user_id", "guest_user"),
        "document_id": state.get("document_id"),
        "image_data": state.get("image_data"),
        "file_data": state.get("file_data")
    }
    rag_result = await rag_agent_app.ainvoke(initial_rag_state)
    answer = rag_result.get("generation", "Tôi không tìm thấy thông tin liên quan trong tài liệu này")
    return {"final_answer": answer, "route": "rag"}

async def billing_node(state: RouterState):
    question = state["question"]
    user_id = state["user_id"] or "guest_user"
    messages = [HumanMessage(content=f"Truy vấn từ ID người dùng <{user_id}>: {question}")]
    try:
        response = await billing_agent_app.ainvoke({"messages": messages})
        answer = response["messages"][-1].content
    except Exception as e:
        logger.error(f"Billing agent error: {e}")
        answer = "Hệ thống tài chính hiện đang bảo trì, vui lòng quay lại sau"
    return {"final_answer": answer, "route": "billing"}

async def workspace_node(state: RouterState):
    question = state["question"]
    user_id = state["user_id"] or "guest_user"
    messages = [HumanMessage(content=f"Truy vấn từ ID người dùng <{user_id}>: {question}")]
    try:
        response = await workspace_agent_app.ainvoke({"messages": messages})
        answer = response["messages"][-1].content
    except Exception as e:
        logger.error(f"Workspace agent error: {e}")
        answer = "Hệ thống quản lý thư viện hiện đang gặp sự cố"
    return {"final_answer": answer, "route": "workspace"}

async def multi_node(state: RouterState):
    question = state["question"]
    user_id = state["user_id"] or "guest_user"
    document_id = state.get("document_id")

    try:
        billing_resp = await billing_agent_app.ainvoke({"messages": [HumanMessage(content=f"Truy vấn từ ID <{user_id}>: Lấy tình trạng ví để phục vụ cho câu hỏi: {question}")]})
        wallet_context = billing_resp["messages"][-1].content
    except Exception:
        wallet_context = "Không thể truy xuất thông tin ví"

    initial_rag_state = {
        "question": f"Tài chính người dùng: {wallet_context}. Câu hỏi: {question}",
        "chat_history": [],
        "generation": "",
        "documents": [],
        "retry_count": 0,
        "hallucination_pass": "yes",
        "use_web": state.get("use_web", False),
        "use_smart": state.get("use_smart", False),
        "user_id": user_id,
        "document_id": document_id
    }
    try:
        rag_result = await rag_agent_app.ainvoke(initial_rag_state)
        answer = rag_result.get("generation", "Tôi không tìm thấy dữ liệu phù hợp trong tài liệu")
    except Exception as e:
        logger.error(f"RAG execution error in multi-node: {e}")
        answer = "Gặp sự cố khi tổng hợp thông tin từ các nguồn dữ liệu"

    return {"final_answer": answer, "route": "multi"}

async def chat_node(state: RouterState):
    prompt = PromptTemplate(
        template="""Bạn là trợ lý ảo thân thiện của DocLib. Trả lời người dùng vui vẻ, ngắn gọn.
        NẾU người dùng yêu cầu tạo file, xuất file, hoặc mã nguồn, hãy bọc nội dung file đó trong markdown code block. Hệ thống sẽ tự tạo nút tải xuống.
        User: {question}""",
        input_variables=["question"]
    )
    try:
        tagged_llm = router_llm.with_config({"tags": ["final_generator"]})
        response = await tagged_llm.ainvoke(prompt.format(question=state["question"]))
        answer = response.content.strip()
    except Exception as e:
        logger.error(f"Chat LLM error: {e}")
        answer = "Chào bạn! DocLib rất vui được hỗ trợ bạn"
    return {"final_answer": answer, "route": "chat"}

def decide_route(state: RouterState):
    return state["route"]

builder = StateGraph(RouterState)
builder.add_node("route_query", route_query)
builder.add_node("rag", rag_node)
builder.add_node("billing", billing_node)
builder.add_node("workspace", workspace_node)
builder.add_node("multi", multi_node)
builder.add_node("chat", chat_node)
builder.set_entry_point("route_query")

builder.add_conditional_edges(
    "route_query",
    decide_route,
    {
        "rag": "rag",
        "billing": "billing",
        "workspace": "workspace",
        "multi": "multi",
        "chat": "chat"
    }
)

builder.add_edge("rag", END)
builder.add_edge("billing", END)
builder.add_edge("workspace", END)
builder.add_edge("multi", END)
builder.add_edge("chat", END)

memory = MemorySaver()
router_agent_app = builder.compile(checkpointer=memory)
