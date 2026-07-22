"""
<module_purpose>
DocLib Orchestration Graph configuring the state machine nodes, edges, and conditions for the LangGraph workflow.
</module_purpose>
<contract>
- Precondition: All necessary tools and models properly initialized.
- Postcondition: Exposes a compiled LangGraph app ready for invocation.
- Error Handling: Implements safety nets, fallback loops, and hallucination checks within the graph topology.
</contract>
"""
import asyncio
import os
from typing import Annotated, List, Literal, Optional, Sequence, TypedDict

import langchain
from langchain_community.cache import RedisCache
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.graph import END, StateGraph
from loguru import logger
from pydantic import BaseModel, Field
from redis import Redis
from src.memory.management import memory_manager

from src.rag.embedding import embedder
from src.rag.retrieval import retriever
from src.store.vector import vector_store
from src.utils.processing import extract_text_from_base64
from src.workflow.state import AgentState

from src.core.infrastructure.configuration import settings

try:
    from sentence_transformers import CrossEncoder

    nli_model_name = settings.NLI_MODEL_NAME
    nli_model = CrossEncoder(nli_model_name)
except Exception as e:
    nli_model = None
    logger.exception("NLI language model loading error")

try:
    from sentence_transformers import CrossEncoder

    reranker = CrossEncoder(settings.RERANKER_MODEL)
except Exception:
    reranker = None

try:
    redis_url = settings.REDIS_URI
    from langchain_community.cache import RedisSemanticCache

    langchain.llm_cache = RedisSemanticCache(
        redis_url=redis_url, embedding=embedder
    )
    logger.info("Redis semantic cache initialized successfully")
except Exception as e:
    logger.exception("Redis semantic cache initialization error")

from huggingface_hub import AsyncInferenceClient
from src.utils.huggingface import HFInferenceChat

llama_client = AsyncInferenceClient(
    model=settings.LLM_MODEL,
    token=settings.HF_TOKEN,
)
llm = HFInferenceChat(client=llama_client, model=settings.LLM_MODEL)

llm_generate = llm.with_config({"tags": ["final_generator"]})

from src.schemas.routing import ContextQuery, GraphRoute, RetrievalStrategy, QueryOptimization
from src.schemas.evaluation import DocumentGrade

async def contextualize_question(state: AgentState):
    question = state["question"]
    history = state.get("chat_history", [])
    if not history:
        return {"question": question}

    history_str = "\n".join([f"{msg['role']} {msg['content']}" for msg in history[-5:]])
    from src.core.registry import PromptType, registry

    prompt = PromptTemplate(
        template=registry.get(PromptType.CONTEXTUALIZE),
        input_variables=["history", "question"],
    )
    try:
        structured_llm = llm.with_structured_output(ContextQuery)
        response = await structured_llm.ainvoke(
            prompt.format(history=history_str, question=question)
        )
        return {"question": response.question}
    except Exception as e:
        logger.exception("Contextualization processing error")
        return {"question": question}

async def route_question(state: AgentState):
    question = state["question"]
    from src.core.registry import PromptType, registry

    prompt = PromptTemplate(
        template=registry.get(PromptType.ROUTE), input_variables=["question"]
    )
    try:
        structured_llm = llm.with_structured_output(GraphRoute)
        response = await structured_llm.ainvoke(prompt.format(question=question))
        return {"current_source": "db", "route": response.route}
    except Exception as e:
        logger.exception("Graph routing execution error")
        return {"current_source": "db", "route": "rag"}

def decide_initial_route(state: AgentState):
    return "generate_direct" if state.get("route") == "direct" else "preprocess_file"

def preprocess_file(state: AgentState):
    updates = {}
    file_data = state.get("file_data")
    if file_data and file_data.startswith("data:"):
        text = extract_text_from_base64(file_data)
        if text:
            updates["file_data"] = text

    folder_data = state.get("folder_data")
    if folder_data and folder_data.startswith("data:"):
        text = extract_text_from_base64(folder_data)
        if text:
            updates["folder_data"] = text

    return updates

def _mask_pii(text: str) -> str:
    import re

    text = re.sub(r"\b(0[3|5|7|8|9])+([0-9]{8})\b", "[REDACTED PHONE]", text)
    text = re.sub(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[REDACTED EMAIL]", text
    )
    text = re.sub(r"\b(?:\d[ -]*?){13,16}\b", "[REDACTED CC]", text)
    return text

async def retrieve_db(state: AgentState):
    question = state["question"]
    document_ids = state.get("document_ids", [])

    if document_ids and len(document_ids) >= 2:
        logger.info("Processing cross-document retrieval")
        try:
            raw_documents = await retriever.cross_document_retrieve(
                question, document_ids, k=6
            )
            extracted_documents = []
            for doc in raw_documents:
                meta = doc.get("metadata", {})
                title = meta.get("title", "Document")
                extracted_documents.append(
                    f"Source document {title}\n{_mask_pii(doc.get('text', ''))}"
                )
            return {"documents": list(set(extracted_documents)), "current_source": "db"}
        except Exception as e:
            logger.exception("Cross-document retrieval execution error")

    from src.core.registry import PromptType, registry

    prompt = PromptTemplate(
        template=registry.get(PromptType.RETRIEVAL_STRATEGY),
        input_variables=["question"],
    )
    queries = [question]
    try:
        structured_llm = llm.with_structured_output(RetrievalStrategy)
        response = await structured_llm.ainvoke(prompt.format(question=question))
        if not response.is_simple and response.queries:
            queries.extend(response.queries)
    except Exception as e:
        logger.exception("Optimal retrieval strategy generation error")

    extracted_documents = []

    all_raw_documents = []
    for q in list(dict.fromkeys(queries))[:3]:
        try:
            results = await vector_store.query(
                query_vector=await embedder.embed_query(q),
                document_ids=document_ids,
                limit=10,
            )
            for doc in results:
                doc["_query"] = q
                all_raw_documents.append(doc)
        except Exception as e:
            logger.exception("Vector similarity search error")

    if all_raw_documents:
        if reranker:
            try:
                pairs = [
                    [doc["_query"], doc.get("text", "")] for doc in all_raw_documents
                ]
                scores = await asyncio.to_thread(reranker.predict, pairs)
                scored_documents = list(zip(all_raw_documents, scores))
                scored_documents.sort(key=lambda x: x[1], reverse=True)
                top_documents = retriever._lost_in_the_middle_reorder(
                    [doc for doc, score in scored_documents[:6]]
                )[:3]
            except Exception as e:
                logger.exception("Search result reordering error via reranker model")
                top_documents = all_raw_documents[:3]
        else:
            top_documents = all_raw_documents[:3]

        for doc in top_documents:
            meta = doc.get("metadata", {})
            title = meta.get("title", "Document")
            extracted_documents.append(
                f"Source document {title}\n{_mask_pii(doc.get('text', ''))}"
            )

    return {"documents": list(set(extracted_documents)), "current_source": "db"}

async def retrieve_internet(state: AgentState):
    from src.agents.engine import search_engine

    question = state["question"]
    try:
        results = await search_engine.execute(question)
        return {
            "documents": [f"[Internet Source]\n{results}"],
            "current_source": "internet",
        }
    except Exception as e:
        logger.exception("Internet search engine execution error")
        return {"documents": [], "current_source": "internet"}

async def grade_documents(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    from src.core.registry import PromptType, registry

    prompt = PromptTemplate(
        template=registry.get(PromptType.GRADE_DOCUMENT),
        input_variables=["context", "question"],
    )
    filtered_documents = []

    structured_llm = llm.with_structured_output(DocumentGrade)

    for d in documents:
        try:
            response = await structured_llm.ainvoke(
                prompt.format(context=d, question=question)
            )
            if response.is_relevant:
                filtered_documents.append(d)
        except Exception as e:
            logger.exception("Document relevance grading error")
            filtered_documents.append(d)
    return {"documents": filtered_documents}

def decide_after_grade(state: AgentState):
    if len(state.get("documents", [])) > 0:
        return "generate"
    if state.get("current_source") == "db" and state.get("use_web"):
        return "retrieve_internet"
    return "generate"

async def transform_query(state: AgentState):
    question = state["question"]
    from src.core.registry import PromptType, registry

    prompt = PromptTemplate(
        template=registry.get(PromptType.OPTIMIZE_QUERY),
        input_variables=["question"],
    )
    try:
        structured_llm = llm.with_structured_output(QueryOptimization)
        res = await structured_llm.ainvoke(prompt.format(question=question))
        return {
            "question": res.question,
            "retry_count": state.get("retry_count", 0) + 1,
            "current_source": "db",
        }
    except Exception as e:
        logger.exception("Search query optimization error")
        return {"retry_count": state.get("retry_count", 0) + 1}

async def generate_direct(state: AgentState):
    from src.core.registry import PromptType, registry

    prompt = registry.get(PromptType.GENERATE_DIRECT).format(
        question=state["question"]
    )
    try:
        response = await llm_generate.ainvoke(prompt)
        return {"generation": response.content}
    except Exception as e:
        logger.exception("AI response synthesis and generation encountered an error")
        return {
            "generation": "Hệ thống gặp sự cố bất ngờ trong quá trình tổng hợp dữ liệu, vui lòng thử lại sau"
        }

async def generate(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    user_id = state.get("user_id")
    if not user_id:
        return {
            "generation": "Yêu cầu cần xác thực quyền truy cập, vui lòng đăng nhập để tiếp tục"
        }
    user_context = await memory_manager.get_user_preferences(user_id)
    if state.get("file_data"):
        documents.append(f"[Attached Personal Documents]\n{state['file_data'][:6000]}")
    if state.get("folder_data"):
        documents.append(f"[Attached Folder Context]\n{state['folder_data'][:6000]}")

    citation_instruction = (
        "CRITICAL: Cite your sources inline by referencing the document title or source name whenever you make a factual claim drawn from the reference documents. Do NOT cite without a corresponding source."
        if documents
        else "CRITICAL: Do NOT include any citations or references — no relevant documents were retrieved for this query. All factual claims must come from your training knowledge only."
    )
    thought_instruction = (
        "Analyze the evidence carefully and provide only the final answer without exposing private reasoning."
        if state.get("use_smart")
        else ""
    )

    from src.core.registry import PromptType, registry

    prompt_text = registry.get(PromptType.SYNTHESIS).format(
        question=question,
        documents="\n\n".join(documents),
        source_name="System" if state.get("current_source") == "db" else "Internet",
        user_context=user_context,
        citation_instruction=citation_instruction,
        thought_instruction=thought_instruction,
    )

    if state.get("image_data"):
        content = [
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": state["image_data"]}},
        ]
    else:
        content = prompt_text

    try:
        response = await llm_generate.ainvoke([HumanMessage(content=content)])
        generation = response.content
        return {"generation": generation}
    except Exception as e:
        logger.exception("Document content generation error")
        return {
            "generation": "Hệ thống gặp sự cố bất ngờ trong quá trình tổng hợp dữ liệu, vui lòng thử lại sau"
        }

async def grade_generation(state: AgentState):
    documents = state.get("documents", [])
    generation = state["generation"]

    if not documents:
        return {"hallucination_pass": "yes"}

    try:
        import asyncio

        from src.agents.reasoning import reasoner

        documents_list = [
            {"text": d, "metadata": {"title": "Source"}} for d in documents
        ]
        eval_res = await reasoner.evaluate_quality(
            state["question"], generation, documents_list
        )

        is_hallucination = eval_res.get("should_retry", False)

        if not is_hallucination and nli_model:
            documents_str = "".join(documents)[:1500]
            scores = await asyncio.to_thread(
                nli_model.predict, [[documents_str, generation]]
            )
            if scores[0][0] > scores[0][1]:
                is_hallucination = True

        return {"hallucination_pass": "no" if is_hallucination else "yes"}
    except Exception as e:
        logger.exception("Generated content hallucination grading error")
        return {"hallucination_pass": "yes"}

def check_hallucination(state: AgentState):
    if state.get("hallucination_pass") == "no" and state.get("retry_count", 0) < 2:
        return "transform_query"
    return END

def decide_after_retrieve(state: AgentState):
    if state.get("use_smart"):
        return "grade_documents"
    if (
        not state.get("documents")
        and state.get("use_web")
        and state.get("current_source") == "db"
    ):
        return "retrieve_internet"
    return "generate"

workflow = StateGraph(AgentState)
workflow.add_node("preprocess_file", preprocess_file)
workflow.add_node("route_question", route_question)
workflow.add_node("retrieve_db", retrieve_db)
workflow.add_node("retrieve_internet", retrieve_internet)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("transform_query", transform_query)
workflow.add_node("generate", generate)
workflow.add_node("generate_direct", generate_direct)
workflow.add_node("grade_generation", grade_generation)
workflow.add_node("contextualize_question", contextualize_question)

workflow.set_entry_point("contextualize_question")

workflow.add_edge("contextualize_question", "route_question")
workflow.add_conditional_edges(
    "route_question",
    decide_initial_route,
    {"preprocess_file": "preprocess_file", "generate_direct": "generate_direct"},
)
workflow.add_edge("preprocess_file", "retrieve_db")
workflow.add_edge("generate_direct", END)
workflow.add_conditional_edges(
    "retrieve_db",
    decide_after_retrieve,
    {
        "grade_documents": "grade_documents",
        "retrieve_internet": "retrieve_internet",
        "generate": "generate",
    },
)
workflow.add_edge("retrieve_internet", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents",
    decide_after_grade,
    {"generate": "generate", "retrieve_internet": "retrieve_internet"},
)
workflow.add_edge("transform_query", "retrieve_db")
workflow.add_conditional_edges(
    "generate",
    lambda s: "grade_generation" if s.get("use_smart") else END,
    {"grade_generation": "grade_generation", END: END},
)
workflow.add_conditional_edges(
    "grade_generation",
    check_hallucination,
    {"transform_query": "transform_query", END: END},
)

knowledge_app = workflow.compile()
