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
from src.memory.manager import memory_manager
from src.memory.mem0_manager import mem0_manager
from src.rag.embedder import embedder
from src.rag.retriever import retriever
from src.store.vector import vector_store
from src.utils.file_processing import extract_text_from_base64
from src.workflow.state import AgentState

from core.infrastructure.app_config import settings

try:
    from sentence_transformers import CrossEncoder

    nli_model_name = settings.NLI_MODEL_NAME
    nli_model = CrossEncoder(nli_model_name)
except Exception:
    nli_model = None
    logger.error("Lỗi tải mô hình ngôn ngữ")


try:
    from sentence_transformers import CrossEncoder

    reranker = CrossEncoder(settings.RERANKER_MODEL)
except Exception:
    reranker = None

try:
    redis_url = settings.REDIS_URI
    from langchain_community.cache import RedisSemanticCache

    langchain.llm_cache = RedisSemanticCache(
        redis_url=redis_url, embedding=embedding_service
    )
    logger.info("Khởi tạo bộ nhớ đệm ngữ nghĩa thành công")
except Exception as e:
    logger.warning("Lỗi khởi tạo bộ nhớ đệm")

from huggingface_hub import AsyncInferenceClient
from src.utils.hf import HFInferenceChat

llama_client = AsyncInferenceClient(
    model=settings.LLAMA_MODEL,
    token=settings.HF_TOKEN,
)
llm = HFInferenceChat(client=llama_client, model=settings.LLAMA_MODEL)

try:
    _fallback_client = AsyncInferenceClient(
        model=settings.FALLBACK_MODEL,
        token=settings.HF_TOKEN,
    )
    _fallback_llm = HFInferenceChat(
        client=_fallback_client, model=settings.FALLBACK_MODEL
    )
    llm = llm.with_fallbacks([_fallback_llm])
    logger.info("Thiết lập dự phòng mô hình ngôn ngữ thành công")
except Exception:
    logger.warning("Lỗi cấu hình mô hình ngôn ngữ thay thế")

llm_generate = llm.with_config({"tags": ["final_generator"]})


class ContextQuery(BaseModel):
    question: str = Field(description="Câu hỏi đã được viết lại")


class GraphRoute(BaseModel):
    route: Literal["rag", "direct"] = Field(
        description="Tuyến đường: 'rag' hoặc 'trực tiếp'"
    )


class RetrievalStrategy(BaseModel):
    is_simple: bool = Field(
        description="Đúng nếu câu hỏi đơn giản, Sai nếu cần truy vấn phụ"
    )
    queries: List[str] = Field(description="Danh sách truy vấn tìm kiếm tối ưu")


class QueryOptimization(BaseModel):
    question: str = Field(description="Lệnh tìm kiếm tối ưu")


class DocumentGrade(BaseModel):
    is_relevant: bool = Field(description="Tài liệu có liên quan đến câu hỏi hay không")


async def contextualize_question(state: AgentState):
    question = state["question"]
    history = state.get("chat_history", [])
    if not history:
        return {"question": question}

    history_str = "\n".join([f"{msg['role']} {msg['content']}" for msg in history[-5:]])
    from src.core.prompt_registry import PromptType, prompt_registry

    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.CONTEXTUALIZE),
        input_variables=["history", "question"],
    )
    try:
        structured_llm = llm.with_structured_output(ContextQuery)
        response = await structured_llm.ainvoke(
            prompt.format(history=history_str, question=question)
        )
        return {"question": response.question}
    except Exception:
        logger.error("Lỗi xử lý ngữ cảnh")
        return {"question": question}


async def route_question(state: AgentState):
    question = state["question"]
    from src.core.prompt_registry import PromptType, prompt_registry

    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.ROUTE), input_variables=["question"]
    )
    try:
        structured_llm = llm.with_structured_output(GraphRoute)
        response = await structured_llm.ainvoke(prompt.format(question=question))
        return {"current_source": "db", "route": response.route}
    except Exception:
        logger.error("Lỗi điều hướng")
        return {"current_source": "db", "route": "rag"}


def decide_initial_route(state: AgentState):
    return "generate_direct" if state.get("route") == "direct" else "preprocess_file"


def preprocess_file(state: AgentState):
    file_data = state.get("file_data")
    if file_data and file_data.startswith("data:"):
        text = extract_text_from_base64(file_data)
        if text:
            return {"file_data": text}
    return {}


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
        logger.info("Đang xử lý tài liệu bằng truy xuất liên kết")
        try:
            raw_documents = await retrieval.cross_document_retrieve(
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
        except Exception:
            logger.error("Lỗi truy xuất tài liệu liên kết")

    from src.core.prompt_registry import PromptType, prompt_registry

    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.RETRIEVAL_STRATEGY),
        input_variables=["question"],
    )
    queries = [question]
    try:
        structured_llm = llm.with_structured_output(RetrievalStrategy)
        response = await structured_llm.ainvoke(prompt.format(question=question))
        if not response.is_simple and response.queries:
            queries.extend(response.queries)
    except Exception:
        logger.error("Lỗi tạo chiến lược truy xuất tối ưu")

    extracted_documents = []

    all_raw_documents = []
    for q in list(dict.fromkeys(queries))[:3]:
        try:
            results = await vector_store.query(
                query_vector=await embedding.embed_query(q),
                document_ids=document_ids,
                limit=10,
            )
            for doc in results:
                doc["_query"] = q
                all_raw_documents.append(doc)
        except Exception:
            logger.error("Lỗi tìm kiếm tương đồng vector")

    if all_raw_documents:
        if reranker:
            try:
                pairs = [
                    [doc["_query"], doc.get("text", "")] for doc in all_raw_documents
                ]
                scores = await asyncio.to_thread(reranker.predict, pairs)
                scored_documents = list(zip(all_raw_documents, scores))
                scored_documents.sort(key=lambda x: x[1], reverse=True)
                top_documents = retrieval._lost_in_the_middle_reorder(
                    [doc for doc, score in scored_documents[:6]]
                )[:3]
            except Exception:
                logger.error("Lỗi sắp xếp kết quả tìm kiếm bằng mô hình xếp hạng")
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
    from src.agents.search_engine import search_engine

    question = state["question"]
    try:
        results = await search_engine.execute(question)
        return {
            "documents": [f"[Internet Source]\n{results}"],
            "current_source": "internet",
        }
    except Exception:
        logger.error("Lỗi tìm kiếm trên web")
        return {"documents": [], "current_source": "internet"}


async def grade_documents(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    from src.core.prompt_registry import PromptType, prompt_registry

    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.GRADE_DOCUMENT),
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
        except Exception:
            logger.error("Lỗi đánh giá mức độ liên quan của tài liệu")
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
    from src.core.prompt_registry import PromptType, prompt_registry

    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.OPTIMIZE_QUERY),
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
    except Exception:
        logger.error("Lỗi tối ưu lệnh tìm kiếm")
        return {"retry_count": state.get("retry_count", 0) + 1}


async def generate_direct(state: AgentState):
    from src.core.prompt_registry import PromptType, prompt_registry

    prompt = prompt_registry.get(PromptType.GENERATE_DIRECT).format(
        question=state["question"]
    )
    try:
        response = await llm_generate.ainvoke(prompt)
        return {"generation": response.content}
    except Exception:
        logger.error("Response generation failed")
        return {
            "generation": "The system encountered an unexpected error during generation and requires you to try again later"
        }


async def generate(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    user_id = state.get("user_id")
    if not user_id:
        return {
            "generation": "Authentication is required to proceed with this specific operation please log in and try again"
        }
    user_context = await memory_manager.get_user_preferences(user_id)
    if state.get("file_data"):
        documents.append(f"[Attached Personal Documents]\n{state['file_data'][:6000]}")

    citation_instruction = (
        "- Use inline source citations when referencing documents"
        if documents
        else "- Do NOT use any citations as no relevant documents were found"
    )
    thought_instruction = (
        "- You MUST present your reasoning, analysis, and outline inside <think></think> tags at the beginning of your response, before delivering the final answer"
        if state.get("use_smart")
        else ""
    )

    from src.core.prompt_registry import PromptType, prompt_registry

    prompt_text = prompt_registry.get(PromptType.SYNTHESIS).format(
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
        await mem0_manager.search_and_resolve_conflicts(question, user_id)
        await mem0_manager.add_memory(
            [
                {"role": "user", "content": question},
                {"role": "assistant", "content": generation},
            ],
            user_id,
        )
        return {"generation": generation}
    except Exception:
        logger.error("Lỗi tạo nội dung tài liệu")
        return {
            "generation": "The system encountered an unexpected error during generation and requires you to try again later"
        }


async def grade_generation(state: AgentState):
    documents = state.get("documents", [])
    generation = state["generation"]

    if not documents:
        return {"hallucination_pass": "yes"}

    try:
        import asyncio

        from src.agents.logical_reasoning import reasoner

        documents_list = [
            {"text": d, "metadata": {"title": "Source"}} for d in documents
        ]
        eval_res = await reasoning.evaluate_quality(
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
    except Exception:
        logger.exception("Lỗi đánh giá nội dung tạo ra")
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
