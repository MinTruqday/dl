import operator
from typing import Annotated, List, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.types import Send

from src.core.infrastructure.configuration import settings

BATCH_SIZE = 5
MAX_CHUNKS = 40

class MapReduceState(TypedDict):
    document_text: str
    chunks: List[str]
    summaries: Annotated[list, operator.add]
    final_summary: str

async def splitter_node(state: MapReduceState):
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=512 * 10,
        chunk_overlap=64 * 3,
    )
    chunks = splitter.split_text(state["document_text"])
    if len(chunks) > MAX_CHUNKS:
        chunks = chunks[:MAX_CHUNKS]
    return {"chunks": chunks}

def map_router(state: MapReduceState):
    return [Send("summarize_node", {"chunk": chunk}) for chunk in state["chunks"]]

class SummarizeState(TypedDict):
    chunk: str

async def summarize_node(state: SummarizeState):
    from langchain_core.messages import HumanMessage
    from src.agents.plan import llm

    from src.core.registry import registry, PromptType
    prompt = registry.get(PromptType.REDUCTION_SEGMENT_SUMMARY).format(chunk=state['chunk'])
    res = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"summaries": [res.content]}

async def hierarchical_reduce_node(state: MapReduceState):
    from langchain_core.messages import HumanMessage
    from src.agents.plan import llm

    summaries = state["summaries"]

    batches = [
        summaries[i : i + BATCH_SIZE] for i in range(0, len(summaries), BATCH_SIZE)
    ]
    mid_summaries = []
    for batch in batches:
        combined = "\n\n---\n\n".join(batch)
        from src.core.registry import registry, PromptType
        prompt = registry.get(PromptType.REDUCTION_FINAL_SUMMARY).format(combined=combined)
        try:
            res = await llm.ainvoke([HumanMessage(content=prompt)])
            mid_summaries.append(res.content)
        except Exception:
            mid_summaries.extend(batch[:2])

    final_combined = "\n\n---\n\n".join(mid_summaries)
    from src.core.registry import registry, PromptType
    final_prompt = registry.get(PromptType.REDUCTION_SYNTHESIS_SUMMARY).format(final_combined=final_combined)
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
    """Use this tool to read and summarize an entire large document (Map-Reduce)"""
    from src.tools.interface import _get_doc_text

    token = config.get("configurable", {}).get("token")
    if not token:
        return "Vui lòng xác thực thông tin tài khoản để tiếp tục quá trình"
    text = await _get_doc_text(document_id, token)
    if not text:
        return "Nội dung gốc của tài liệu hiện không khả dụng"

    res = await map_reduce_app.ainvoke(
        {"document_text": text, "chunks": [], "summaries": [], "final_summary": ""}
    )
    return f"Tiến trình tổng hợp tài liệu hoàn tất\n\n{res['final_summary']}"
