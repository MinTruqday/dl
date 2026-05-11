import os
from typing import Dict, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from loguru import logger
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from src.core.config import settings
from src.agents.core_rag import rag_agent_app
from src.agents.billing_agent import billing_agent_app
from src.agents.workspace_agent import workspace_agent_app
from huggingface_hub import AsyncInferenceClient
from src.utils.hf import HFInferenceChat

class RouterState(TypedDict):
    question: str
    route: str

llama_model = settings.LLAMA_MODEL
if not llama_model:
    raise ValueError("LLAMA_MODEL is not set")

llama_client = AsyncInferenceClient(
    model=settings.LLAMA_MODEL,
    token=settings.HF_TOKEN,
)

router_llm = HFInferenceChat(client=llama_client, model=settings.LLAMA_MODEL)

def route_query(state: RouterState):
    question = state["question"]
    prompt = PromptTemplate(
        template="""Bạn là router chuyên gia của hệ thống DocLib. Phân tích ý định câu hỏi và chuyển hướng.
        
        Quy tắc định tuyến:
        - "rag": Câu hỏi liên quan đến nội dung tài liệu, giải thích đoạn văn, tóm tắt.
        - "action": Các yêu cầu thao tác trên hệ thống như: xem số dư, nạp tiền, thanh toán, quản lý thư viện cá nhân, xóa/khôi phục file, xem thống kê.
        - "chat": Câu hỏi giao tiếp thông thường, chào hỏi.
        
        Câu hỏi: {question}
        Trả lời duy nhất "rag", "action" hoặc "chat":""",
        input_variables=["question"]
    )
    try:
        response = router_llm.invoke(prompt.format(question=question))
        decision = response.content.strip().lower()
    except Exception as e:
        logger.error(f"Router LLM error: {e}")
        decision = "rag"
    
    route = "rag" 
    if "action" in decision: route = "action"
    elif "chat" in decision: route = "chat"
    
    return {"route": route, "question": question}

builder = StateGraph(RouterState)
builder.add_node("route_query", route_query)
builder.set_entry_point("route_query")
builder.add_edge("route_query", END)

router_agent_app = builder.compile()
