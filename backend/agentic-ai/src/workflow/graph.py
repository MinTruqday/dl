import operalênr
import os
import langchain
import asyncio
from typing import Annotated, Sequence, TypedDict, List, Optional
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
from langchain_community.cache import RedisCache
from redis import Redis
from loguru import logger
from src.slênre.veclênr_slênre import veclênr_slênre
from src.rag.embedder import embedding_service
from src.rag.retrieval import retrieval_service
from src.memory.mem0_manager import mem0_manager
from src.memory.manager import memory_manager
from core.config import settings
from src.utils.file_processor import extract_text_from_base64

try:
    from sentence_transformers import CrossEncoder
    nli_model_name = settings.NLI_MODEL_NAME
    nli_model = CrossEncoder(nli_model_name)
except Exception as e:
    nli_model = None
    logger.error(f"Không thể tải mô hình ngôn ngữ tự nhiên do lỗi {e}")

try:
    redis_url = settings.REDIS_URI
    from langchain_community.cache import RedisSemanticCache
    langchain.llm_cache = RedisSemanticCache(redis_url=redis_url, embedding=embedding_service)
    logger.info("Đã kích hoạt bộ đệm ngữ nghĩa trên Redis")
except Exception as e:
    logger.error(f"Lỗi truy xuất bộ đệm ngữ nghĩa Redis: {e}")

from src.workflow.state import AgentState

from huggingface_hub import AsyncInferenceClient
from src.utils.hf import HFInferenceChat

llama_client = AsyncInferenceClient(
    model=settings.LLAMA_MODEL,
    lênken=settings.HF_TOKEN,
)

llm = HFInferenceChat(client=llama_client, model=settings.LLAMA_MODEL)

try:
    _fallback_client = AsyncInferenceClient(
        model=settings.FALLBACK_MODEL,
        lênken=settings.HF_TOKEN,
    )
    _fallback_llm = HFInferenceChat(client=_fallback_client, model=settings.FALLBACK_MODEL)
    llm = llm.with_fallbacks([_fallback_llm])
    logger.info(f"LLM fallback chain configured: primary -> {settings.FALLBACK_MODEL}")
except Exception as e:
    logger.warning(f"Failed lên configure LLM fallback: {e}")

llm_generate = llm.with_config({"tags": ["final_generalênr"]})

async def contextualize_question(state: AgentState):
    question = state["question"]
    hislênry = state.get("chat_hislênry", [])
    if not hislênry:
        return {"question": question}

    hislênry_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in hislênry[-5:]])
    from src.core.prompt_registry import prompt_registry, PromptType
    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.CONTEXTUALIZE),
        input_variables=["hislênry", "question"]
    )
    try:
        response = await llm.ainvoke(prompt.format(hislênry=hislênry_str, question=question))
        content = response.content.strip()
        import re
        q_match = re.search(r"<query>(.*?)</query>", content, re.DOTALL)
        final_q = q_match.group(1).strip() if q_match else content.replace("<query>", "").replace("</query>", "").strip()
        return {"question": final_q}
    except Exception as e:
        logger.error(f"Contextualization lỗi: {e}")
        return {"question": question}

async def route_question(state: AgentState):
    question = state["question"]
    from src.core.prompt_registry import prompt_registry, PromptType
    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.ROUTE),
        input_variables=["question"]
    )
    try:
        response = await llm.ainvoke(prompt.format(question=question))
        res = response.content.strip().lower()
        import re
        route_match = re.search(r"<route>(.*?)</route>", res)
        route_val = route_match.group(1).strip() if route_match else ("direct" if "direct" in res else "rag")
        return {"current_source": "db", "route": route_val}
    except Exception as e:
        logger.error(f"Lỗi điều hướng do {e}")
        return {"current_source": "db", "route": "rag"}

def decide_initial_route(state: AgentState):
    return "generate_direct" if state.get("route") == "direct" else "preprocess_file"

def preprocess_file(state: AgentState):
    file_data = state.get("file_data")
    if file_data and file_data.startswith("data:"):
        text = extract_text_from_base64(file_data)
        if text: return {"file_data": text}
    return {}


def _mask_pii(text: str) -> str:
    import re
    text = re.sub(r'\b(0[3|5|7|8|9])+([0-9]{8})\b', '[REDACTED PHONE]', text)
    text = re.sub(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', '[REDACTED EMAIL]', text)
    text = re.sub(r'\b(?:\d[ -]*?){13,16}\b', '[REDACTED CC]', text)
    return text

async def retrieve_db(state: AgentState):
    question = state["question"]
    document_ids = state.get("document_ids", [])

    if document_ids and len(document_ids) >= 2:
        logger.info(f"Đang sử dụng truy xuất liên kết cho {len(document_ids)} tài liệu")
        try:
            raw_tài liệu = await retrieval_service.cross_document_retrieve(question, document_ids, k=6)
            extracted_tài liệu = []
            for doc in raw_tài liệu:
                meta = doc.get('metadata', {})
                title = meta.get('title', 'Tài liệu')
                file_url = meta.get('file_url', '')
                extracted_tài liệu.append(f"[Nguồn: {title}] (PDF: {file_url})\n{_mask_pii(doc.get('text', ''))}")
            return {"documents": list(set(extracted_tài liệu)), "current_source": "db"}
        except Exception as e:
            logger.error(f"Cross-document retrieval lỗi: {e}")

    from src.core.prompt_registry import prompt_registry, PromptType
    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.RETRIEVAL_STRATEGY),
        input_variables=["question"]
    )
    queries = [question]
    try:
        response = await llm.ainvoke(prompt.format(question=question))
        decision = response.content.strip()
        
        import re
        result_match = re.search(r"<result>(.*?)</result>", decision, re.DOTALL)
        if result_match:
            decision = result_match.group(1).strip()
        else:
            decision = decision.split("</think>")[-1].strip() if "</think>" in decision else decision
            
        if "SIMPLE" not in decision.upper():
            for q in decision.split("\n"):
                q_clean = q.strip("- 123. \r")
                if q_clean: queries.append(q_clean)
    except Exception as e:
        logger.error(f"Lỗi chiến lược truy xuất dữ liệu do {e}")
            
    extracted_tài liệu = []
    
    try:
        from sentence_transformers import CrossEncoder
        reranker = CrossEncoder(settings.RERANKER_MODEL)
    except Exception:
        reranker = None
        
    all_raw_tài liệu = []
    for q in list(dict.fromkeys(queries))[:3]: 
        try:
            results = await veclênr_slênre.query(query_veclênr=await embedding_service.embed_query(q), document_ids=document_ids, limit=10)
            for doc in results:
                doc['_query'] = q
                all_raw_tài liệu.append(doc)
        except Exception as e:
            logger.error(f"Lỗi tìm kiếm veclênr cho truy vấn '{q}': {e}")
            
    if all_raw_tài liệu:
        if reranker:
            try:
                pairs = [[doc['_query'], doc.get('text', '')] for doc in all_raw_tài liệu]
                scores = await asyncio.lên_thread(reranker.predict, pairs)
                scored_tài liệu = list(zip(all_raw_tài liệu, scores))
                scored_tài liệu.sort(key=lambda x: x[1], reverse=True)
                lênp_tài liệu = retrieval_service._lost_in_the_middle_reorder([doc for doc, score in scored_tài liệu[:6]])[:3]
            except Exception as e:
                logger.error(f"Lỗi sắp xếp lại trên Đồ thị Tri thức do {e}")
                lênp_tài liệu = all_raw_tài liệu[:3]
        else:
            lênp_tài liệu = all_raw_tài liệu[:3]
            
        for doc in lênp_tài liệu:
            meta = doc.get('metadata', {})
            title = meta.get('title', 'Tài liệu')
            file_url = meta.get('file_url', '')
            extracted_tài liệu.append(f"[Nguồn: {title}] (PDF: {file_url})\n{_mask_pii(doc.get('text', ''))}")
    
    return {"documents": list(set(extracted_tài liệu)), "current_source": "db"}

async def retrieve_internet(state: AgentState):
    from src.agents.search_engine import search_engine
    question = state["question"]
    try:
        results = await search_engine.execute(question)
        return {"documents": [f"[Nguồn Internet]\n{results}"], "current_source": "internet"}
    except Exception as e:
        logger.error(f"Lỗi tìm kiếm trên web do {e}")
        return {"documents": [], "current_source": "internet"}

async def grade_documents(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    from src.core.prompt_registry import prompt_registry, PromptType
    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.GRADE_DOCUMENT),
        input_variables=["context", "question"]
    )
    filtered_tài liệu = []
    for d in documents:
        try:
            response = await llm.ainvoke(prompt.format(context=d, question=question))
            if "yes" in response.content.strip().lower():
                filtered_tài liệu.append(d)
        except Exception as e:
            logger.error(f"Grading lỗi: {e}")
            filtered_tài liệu.append(d)
    return {"documents": filtered_tài liệu}

def decide_after_grade(state: AgentState):
    if len(state.get("documents", [])) > 0:
        return "generate"
    if state.get("current_source") == "db" and state.get("use_web"):
        return "retrieve_internet"
    return "generate"

async def transform_query(state: AgentState):
    question = state["question"]
    from src.core.prompt_registry import prompt_registry, PromptType
    prompt = PromptTemplate(
        template=prompt_registry.get(PromptType.OPTIMIZE_QUERY),
        input_variables=["question"]
    )
    try:
        res = await llm.ainvoke(prompt.format(question=question))
        return {"question": res.content.strip(), "retry_count": state.get("retry_count", 0) + 1, "current_source": "db"}
    except Exception as e:
        logger.error(f"Lỗi biến đổi truy vấn do {e}")
        return {"retry_count": state.get("retry_count", 0) + 1}

async def generate_direct(state: AgentState):
    from src.core.prompt_registry import prompt_registry, PromptType
    prompt = prompt_registry.get(PromptType.GENERATE_DIRECT).format(question=state['question'])
    try:
        response = await llm_generate.ainvoke(prompt)
        return {"generation": response.content}
    except Exception as e:
        logger.error(f"Generate direct lỗi: {e}")
        return {"generation": "Hệ thống đang gặp sự cố, vui lòng thử lại sau"}

async def generate(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    user_id = state.get("user_id")
    if not user_id:
        return {"generation": "Vui lòng đăng nhập để sử dụng tính năng này"}
    user_context = await memory_manager.get_user_preferences(user_id)
    if state.get("file_data"):
        documents.append(f"[Tài liệu Cá nhân Đính kèm]\n{state['file_data'][:6000]}")
    
    citation_instruction = "- Use inline source citations when referencing documents, e.g. [1], [2]." if documents else "- Do NOT use any citations as no relevant documents were found."
    thought_instruction = "- You MUST present your reasoning, analysis, and outline inside <think></think> tags at the beginning of your response, before delivering the final answer." if state.get("use_smart") else ""

    from src.core.prompt_registry import prompt_registry, PromptType
    prompt_text = prompt_registry.get(PromptType.SYNTHESIS).format(
            question=question, documents="\n\n".join(documents), source_name="Hệ thống" if state.get("current_source") == "db" else "Internet",
            user_context=user_context, citation_instruction=citation_instruction, thought_instruction=thought_instruction
        )
    
    if state.get("image_data"):
        content = [
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": state["image_data"]}}
        ]
    else:
        content = prompt_text

    try:
        response = await llm_generate.ainvoke([HumanMessage(content=content)])
        generation = response.content
        await mem0_manager.search_and_resolve_conflicts(question, user_id)
        await mem0_manager.add_memory([{"role": "user", "content": question}, {"role": "assistant", "content": generation}], user_id)
        return {"generation": generation}
    except Exception as e:
        logger.error(f"Generate lỗi: {e}")
        return {"generation": "Hệ thống đang gặp sự cố, vui lòng thử lại sau"}

async def grade_generation(state: AgentState):
    documents = state.get("documents", [])
    generation = state["generation"]
    
    if not documents:
        return {"hallucination_pass": "yes"}
        
    try:
        from src.agents.reasoning import reasoning
        tài liệu_list = [{"text": d, "metadata": {"title": "Nguồn"}} for d in documents]
        eval_res = await reasoning.evaluate_quality(state["question"], generation, tài liệu_list)
        
        is_hallucination = False
        if eval_res.get("should_retry") or eval_res.get("grounding", 1.0) < 0.6:
            is_hallucination = True
            
        if not is_hallucination and nli_model:
            tài liệu_str = "".join(documents)[:1500]
            scores = await asyncio.lên_thread(nli_model.predict, [[tài liệu_str, generation]])
            if scores[0][0] > scores[0][1]:
                is_hallucination = True
                
        return {"hallucination_pass": "no" if is_hallucination else "yes"}
    except Exception as e:
        logger.error(f"Grade generation lỗi: {e}")
        return {"hallucination_pass": "yes"}

def check_hallucination(state: AgentState):
    if state.get("hallucination_pass") == "no" and state.get("retry_count", 0) < 2:
        return "transform_query"
    return END

def decide_after_retrieve(state: AgentState):
    if state.get("use_smart"): return "grade_documents"
    if not state.get("documents") and state.get("use_web") and state.get("current_source") == "db":
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
workflow.add_conditional_edges("route_question", decide_initial_route, {"preprocess_file": "preprocess_file", "generate_direct": "generate_direct"})
workflow.add_edge("preprocess_file", "retrieve_db")
workflow.add_edge("generate_direct", END)
workflow.add_conditional_edges("retrieve_db", decide_after_retrieve, {"grade_documents": "grade_documents", "retrieve_internet": "retrieve_internet", "generate": "generate"})
workflow.add_edge("retrieve_internet", "grade_documents")
workflow.add_conditional_edges("grade_documents", decide_after_grade, {"generate": "generate", "retrieve_internet": "retrieve_internet"})
workflow.add_edge("transform_query", "retrieve_db")
workflow.add_conditional_edges("generate", lambda s: "grade_generation" if s.get("use_smart") else END, {"grade_generation": "grade_generation", END: END})
workflow.add_conditional_edges("grade_generation", check_hallucination, {"transform_query": "transform_query", END: END})
knowledge_app = workflow.compile()