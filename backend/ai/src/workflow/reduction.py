import json
from typing import Annotated, TypedDict

from langchain_core.tools import tool
from langgraph.graph import END, StateGraph
from langgraph.types import Send
from pydantic import Field


BATCH_SIZE = 5
MAX_CHUNKS = 40

from src.schemas.workflow import MapReduceState

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
    from src.agents.react.planning import llm

    from src.core.registry import registry, PromptType
    prompt = registry.get(PromptType.REDUCTION_SEGMENT_SUMMARY).format(chunk=state['chunk'])
    res = await llm.ainvoke([HumanMessage(content=prompt)])
    return {"summaries": [res.content]}

async def hierarchical_reduce_node(state: MapReduceState):
    from langchain_core.messages import HumanMessage
    from src.agents.react.planning import llm

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
async def agent_summarize_long_document(
    document_id: Annotated[str, Field(description="Exact identifier of the long document to summarize completely")],
    config: dict,
) -> str:
    """
    <module_purpose>Use this tool to read and summarize an entire large document using a Map-Reduce workflow. Use this when the user asks for a comprehensive summary, overview, or tl;dr of a very long document where simple reading might exceed token limits.</module_purpose>
    <contract>Requires the exact document ID.</contract>
    """
    from src.tools.document import _get_doc_text

    token = config.get("configurable", {}).get("token")
    if not token:
        return json.dumps({"status": "authentication_required"})
    text = await _get_doc_text(document_id, token)
    if not text:
        return json.dumps({"status": "document_content_unavailable"})

    res = await map_reduce_app.ainvoke(
        {"document_text": text, "chunks": [], "summaries": [], "final_summary": ""}
    )
    return json.dumps(
        {"status": "success", "summary": res["final_summary"]},
        ensure_ascii=False,
    )
