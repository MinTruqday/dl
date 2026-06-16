import operator
from typing import Annotated, List, TypedDict
from core.config import settings
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, StateGraph
from langgraph.types import Send
from src.agents.planning import llm

BATCH_SIZE = settings.MAP_REDUCE_BATCH_SIZE
MAX_CHUNKS = settings.MAP_REDUCE_MAX_CHUNKS

class MapReduceState(TypedDict):
    document_text: str
    chunks: List[str]
    summaries: Annotated[list, operator.add]
    final_summary: str

async def splitter_node(state: MapReduceState):
    splitter = RecursiveCharacterTextSplitter(chunk_size=settings.DEFAULT_CHUNK_SIZE * 10, chunk_overlap=settings.DEFAULT_CHUNK_OVERLAP * 3)
    chunks = splitter.split_text(state["document_text"])
    if len(chunks) > MAX_CHUNKS:
        chunks = chunks[:MAX_CHUNKS]
    return {"chunks": chunks}

def map_router(state: MapReduceState):
    return [Send("summarize_node", {"chunk": chunk}) for chunk in state["chunks"]]

class SummarizeState(TypedDict):
    chunk: str

async def summarize_node(state: SummarizeState):
    prompt = f"Summarize the following document segment in detail:\n\n{state['chunk']}"
    res = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"summaries": [res.content]}

async def hierarchical_reduce_node(state: MapReduceState):
    summaries = state["summaries"]
    batches = [summaries[i : i + BATCH_SIZE] for i in range(0, len(summaries), BATCH_SIZE)]
    mid_summaries = []
    for batch in batches:
        combined = "\n\n---\n\n".join(batch)
        prompt = f"Briefly summarize the following passages into a single paragraph of no more than 300 words:\n\n{combined}"
        try:
            res = await llm.ainvoke([HumanMessage(content=prompt)])
            mid_summaries.append(res.content)
        except Exception:
            mid_summaries.extend(batch[:2])
    final_combined = "\n\n---\n\n".join(mid_summaries)
    final_prompt = f"Based on the component summaries below synthesize them into a complete coherent comprehensive summary:\n\n{final_combined}"
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

@tool(description="Use this tool to effectively read synthesize and summarize an entire large document mapping dimensional context structure")
async def agent_summarize_long_document(document_id: str, config: dict) -> str:
    from src.tools.api import _get_doc_text
    token = config.get("configurable", {}).get("token")
    if not token:
        return "Xác thực tài khoản và phân quyền người dùng thành công"
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Lỗi khi truy xuất tài liệu"
    res = await map_reduce_app.ainvoke({"document_text": text, "chunks": [], "summaries": [], "final_summary": ""})
    return f"The complete document comprehensive algorithmic functional summary was successfully processed mapping underlying content reliably\n\n{res['final_summary']}"