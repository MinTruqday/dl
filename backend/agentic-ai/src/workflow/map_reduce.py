from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import operator
from langgraph.types import Send
from langchain_core.tools import tool

class MapReduceState(TypedDict):
    document_text: str
    chunks: List[str]
    summaries: Annotated[list, operator.add]
    final_summary: str

async def splitter_node(state: MapReduceState):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=6000, chunk_overlap=200)
    chunks = splitter.split_text(state["document_text"])
    return {"chunks": chunks}

def map_router(state: MapReduceState):
    return [Send("summarize_node", {"chunk": chunk}) for chunk in state["chunks"]]

class SummarizeState(TypedDict):
    chunk: str

async def summarize_node(state: SummarizeState):
    from src.workflow.brain import llm
    from langchain_core.messages import HumanMessage
    prompt = f"Tóm tắt chi tiết đoạn tài liệu sau đây bằng tiếng Việt:\n\n{state['chunk']}"
    res = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"summaries": [res.content]}

async def reduce_node(state: MapReduceState):
    from src.workflow.brain import llm
    from langchain_core.messages import HumanMessage
    combined = "\n\n---\n\n".join(state["summaries"])
    prompt = f"Dựa vào các bản tóm tắt thành phần dưới đây, hãy tổng hợp thành một bản tóm tắt hoàn chỉnh, mạch lạc và đầy đủ thông tin nhất:\n\n{combined}"
    res = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"final_summary": res.content}

mr_graph = StateGraph(MapReduceState)
mr_graph.add_node("splitter", splitter_node)
mr_graph.add_node("summarize_node", summarize_node)
mr_graph.add_node("reduce", reduce_node)

mr_graph.set_entry_point("splitter")
mr_graph.add_conditional_edges("splitter", map_router, ["summarize_node"])
mr_graph.add_edge("summarize_node", "reduce")
mr_graph.add_edge("reduce", END)

map_reduce_app = mr_graph.compile()

@tool
async def agent_summarize_long_document(document_id: str, config: dict) -> str:
    """Sử dụng công cụ này để đọc và tóm tắt toàn bộ một tài liệu khổng lồ (Map-Reduce)."""
    from src.tools.actions import _get_doc_text
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Không tìm thấy token."
    text = await _get_doc_text(document_id, token)
    if not text: return "Không tìm thấy nội dung tài liệu."
    
    res = await map_reduce_app.ainvoke({"document_text": text, "chunks": [], "summaries": [], "final_summary": ""})
    return f"Bản tóm tắt toàn bộ tài liệu:\n\n{res['final_summary']}"
