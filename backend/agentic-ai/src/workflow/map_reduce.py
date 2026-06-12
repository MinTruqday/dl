from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Annotated
import operator
from langgraph.types import Send
from langchain_core.tools import tool

BATCH_SIZE = 5
MAX_CHUNKS = 40

class MapReduceState(TypedDict):
    document_text: str
    chunks: List[str]
    summaries: Annotated[list, operator.add]
    final_summary: str

async def splitter_node(state: MapReduceState):
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(chunk_size=6000, chunk_overlap=200)
    chunks = splitter.split_text(state["document_text"])
    if len(chunks) > MAX_CHUNKS:
        chunks = chunks[:MAX_CHUNKS]
    return {"chunks": chunks}

def map_router(state: MapReduceState):
    return [Send("summarize_node", {"chunk": chunk}) for chunk in state["chunks"]]

class SummarizeState(TypedDict):
    chunk: str

async def summarize_node(state: SummarizeState):
    from src.agents.planning import llm
    from langchain_core.messages import HumanMessage
    prompt = f"Tóm tắt chi tiết đoạn tài liệu sau đây bằng tiếng Việt:\n\n{state['chunk']}"
    res = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"summaries": [res.content]}

async def hierarchical_reduce_node(state: MapReduceState):
    from src.agents.planning import llm
    from langchain_core.messages import HumanMessage
    summaries = state["summaries"]

    batches = [summaries[i:i + BATCH_SIZE] for i in range(0, len(summaries), BATCH_SIZE)]
    mid_summaries = []
    for batch in batches:
        combined = "\n\n---\n\n".join(batch)
        prompt = f"Tóm tắt ngắn gọn các đoạn dưới đây thành một đoạn chứ không quá 300 từ:\n\n{combined}"
        try:
            res = await llm.ainvoke([HumanMessage(content=prompt)])
            mid_summaries.append(res.content)
        except Exception:
            mid_summaries.extend(batch[:2])

    final_combined = "\n\n---\n\n".join(mid_summaries)
    final_prompt = (
        "Dựa vào các bản tóm tắt thành phần dưới đây, hãy tổng hợp thành một bản tóm tắt hoàn chỉnh, "
        f"mạch lạc và đầy đủ thông tin nhất:\n\n{final_combined}"
    )
    res = await llm.ainvoke([HumanMessage(content=final_prompt)])
    return {"final_summary": res.content}

mr_graph = StateGraph(MapReduceState)
mr_graph.add_node("splitter", splitter_node)
mr_graph.add_node("summarize_node", summarize_node)
mr_graph.add_node("reduce", hierarchical_reduce_node)

mr_graph.set_entry_point("splitter")
mr_graph.add_conditional_edges("splitter", map_router, ["summarize_node"])
mr_graph.add_edge("summarize_node", "reduce")
mr_graph.add_edge("reduce", END)

map_reduce_app = mr_graph.compile()

@tool
async def agent_summarize_long_document(document_id: str, config: dict) -> str:
    """Sử dụng công cụ này để đọc và tóm tắt toàn bộ một tài liệu khổng lồ (Map-Reduce)"""
    from src.tools.api_tools import _get_doc_text
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Lỗi xác thực: Không tìm thấy token"
    text = await _get_doc_text(document_id, token)
    if not text: return "Không tìm thấy nội dung tài liệu"
    
    res = await map_reduce_app.ainvoke({"document_text": text, "chunks": [], "summaries": [], "final_summary": ""})
    return f"Bản tóm tắt toàn bộ tài liệu:\n\n{res['final_summary']}"
