import operator
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
from src.store.vector_store import vector_store
from src.ingestion.embedder import embedding_service
from src.agents.retrieval import retrieval_agent
from src.memory.mem0_manager import mem0_manager
from src.memory.manager import memory_manager
from src.core.config import settings
from src.utils.file_processor import extract_text_from_base64

try:
    from sentence_transformers import CrossEncoder
    nli_model_name = settings.NLI_MODEL_NAME
    nli_model = CrossEncoder(nli_model_name)
except Exception as e:
    nli_model = None
    logger.error(f"NLI model load error: {e}")

try:
    redis_url = settings.REDIS_URI
    langchain.llm_cache = RedisCache(redis_=Redis.from_url(redis_url))
except Exception as e:
    logger.error(f"Redis cache error: {e}")

from src.models.state import AgentState

from huggingface_hub import AsyncInferenceClient
from src.utils.hf import HFInferenceChat

llama_client = AsyncInferenceClient(
    model=settings.LLAMA_MODEL,
    token=settings.HF_TOKEN,
)

llm = HFInferenceChat(client=llama_client, model=settings.LLAMA_MODEL)
llm_generate = llm.with_config({"tags": ["final_generator"]})

async def contextualize_question(state: AgentState):
    question = state["question"]
    history = state.get("chat_history", [])
    if not history:
        return {"question": question}

    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]])
    prompt = PromptTemplate(
        template="""SYSTEM IDENTITY: DocLib Core System - Contextualization Engine.
OBJECTIVE: Reconstruct the latest user query into an independent, fully contextualized query by performing anaphora and co-reference resolution based on the conversation history.
OUTPUT_LANGUAGE: Must exactly match the language of the user's input query.

RULES:
- Resolve all ambiguous pronouns and contextual references into explicit entities.
- Wrap the final reconstructed query inside <query>...</query> XML tags.
- Provide no additional conversational text.

<example>
<history>user: Where is the ReactJS tutorial document?</history>
<user_input>Who is its author?</user_input>
<output>
<query>Who is the author of the ReactJS tutorial document?</query>
</output>
</example>

CONVERSATION HISTORY:
{history}

LATEST USER INPUT: {question}
OUTPUT:""",
        input_variables=["history", "question"]
    )
    try:
        response = await llm.ainvoke(prompt.format(history=history_str, question=question))
        content = response.content.strip()
        import re
        q_match = re.search(r"<query>(.*?)</query>", content, re.DOTALL)
        final_q = q_match.group(1).strip() if q_match else content.replace("<query>", "").replace("</query>", "").strip()
        return {"question": final_q}
    except Exception as e:
        logger.error(f"Contextualization error: {e}")
        return {"question": question}

async def route_question(state: AgentState):
    question = state["question"]
    prompt = PromptTemplate(
        template="""SYSTEM IDENTITY: DocLib Core System - Secondary Router.
OBJECTIVE: Classify the query into either an internal database search or a direct response.

ROUTES:
- <route>rag</route>: The query requires retrieving factual data, company procedures, technical documents, or specific file contents.
- <route>direct</route>: The query is general knowledge, conversational, or does not require retrieving specific internal documents.

RULES:
- Provide reasoning inside <think>...</think> tags.
- Output the route inside <route>...</route> tags.

<example>
<user_input>What is the process for uploading documents to DocLib?</user_input>
<output>
<think>This requires internal system documentation regarding upload procedures.</think>
<route>rag</route>
</output>
</example>

USER INPUT: "{question}"
OUTPUT:""",
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
        logger.error(f"Routing error: {e}")
        return {"current_source": "db", "route": "rag"}

def decide_initial_route(state: AgentState):
    return "generate_direct" if state.get("route") == "direct" else "preprocess_file"

def preprocess_file(state: AgentState):
    file_data = state.get("file_data")
    if file_data and file_data.startswith("data:"):
        text = extract_text_from_base64(file_data)
        if text: return {"file_data": text}
    return {}

async def retrieve_db(state: AgentState):
    question = state["question"]
    document_id = state.get("document_id")
    prompt = PromptTemplate(
        template="""SYSTEM IDENTITY: DocLib Core System - Search Strategy Engine.
OBJECTIVE: Decompose the user query into optimal search paths using a Tree of Thoughts approach.
OUTPUT_LANGUAGE: Must exactly match the language of the user's input query.

RULES:
1. Analyze if the query is simple (1 path) or complex (multiple paths). Wrap reasoning in <think>...</think>.
2. Wrap the search strategy in <result>...</result>.
- If simple: output exactly <result>SIMPLE</result>.
- If complex: output the decomposed sub-queries, one per line, inside the <result> tags.

<example>
<user_input>Compare the features of DocLib Basic and Premium plans.</user_input>
<output>
<think>The query addresses two distinct entities: Basic plan and Premium plan features. Decomposition is required.</think>
<result>
Features of the Basic plan
Features of the Premium plan
</result>
</output>
</example>

USER INPUT: "{question}"
OUTPUT:""",
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
        logger.error(f"Retrieval strategy error: {e}")
            
    extracted_docs = []
    for q in list(dict.fromkeys(queries))[:3]: 
        try:
            results = await vector_store.search(query_vector=await embedding_service.embed_query(q), limit=3)
            for doc in results:
                extracted_docs.append(f"[Nguồn: {doc.payload.get('title', 'Tài liệu')}]\n{doc.payload.get('text', '')}")
        except Exception as e:
            logger.error(f"Vector search error for query '{q}': {e}")
    
    return {"documents": list(set(extracted_docs)), "current_source": "db"}

async def retrieve_internet(state: AgentState):
    from src.integrations.search_engine import search_engine_agent
    question = state["question"]
    try:
        results = await search_engine_agent.execute(question)
        return {"documents": [f"[Nguồn Internet]\n{results}"], "current_source": "internet"}
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return {"documents": [], "current_source": "internet"}

async def grade_documents(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    prompt = PromptTemplate(
        template="""SYSTEM IDENTITY: DocLib Core System - Document Grading Engine.
OBJECTIVE: Evaluate whether the provided document contains information relevant to answering the user's query.
OUTPUT_LANGUAGE: Exact string match.

RULES:
- Return 'yes' if the document is relevant or helpful.
- Return 'no' if the document is completely irrelevant.
- Output ONLY 'yes' or 'no'.

DOCUMENT: {context}
USER QUERY: {question}
CONCLUSION:""",
        input_variables=["context", "question"]
    )
    filtered_docs = []
    for d in documents:
        try:
            response = await llm.ainvoke(prompt.format(context=d, question=question))
            if "yes" in response.content.strip().lower():
                filtered_docs.append(d)
        except Exception as e:
            logger.error(f"Grading error: {e}")
            filtered_docs.append(d)
    return {"documents": filtered_docs}

def decide_after_grade(state: AgentState):
    if len(state.get("documents", [])) > 0:
        return "generate"
    if state.get("current_source") == "db" and state.get("use_web"):
        return "retrieve_internet"
    return "generate"

async def transform_query(state: AgentState):
    question = state["question"]
    prompt = PromptTemplate(
        template="""SYSTEM IDENTITY: DocLib Core System - Query Optimization Engine.
OBJECTIVE: Rewrite the given query to maximize vector search retrieval performance.
OUTPUT_LANGUAGE: Must exactly match the language of the user's input query.

RULES:
- Extract key entities, concepts, and remove stop words.
- Output ONLY the optimized query.

ORIGINAL QUERY: {question}
OPTIMIZED QUERY:""",
        input_variables=["question"]
    )
    try:
        res = await llm.ainvoke(prompt.format(question=question))
        return {"question": res.content.strip(), "retry_count": state.get("retry_count", 0) + 1, "current_source": "db"}
    except Exception as e:
        logger.error(f"Transform query error: {e}")
        return {"retry_count": state.get("retry_count", 0) + 1}

async def generate_direct(state: AgentState):
    prompt = f"""SYSTEM IDENTITY: DocLib Core System - Direct Response Engine.
OBJECTIVE: Provide a helpful and conversational response to the user.
OUTPUT_LANGUAGE: Must exactly match the language of the user's input query.

USER QUERY: {state['question']}
RESPONSE:"""
    try:
        response = await llm_generate.ainvoke(prompt)
        return {"generation": response.content}
    except Exception as e:
        logger.error(f"Generate direct error: {e}")
        return {"generation": "Hệ thống đang gặp sự cố, vui lòng thử lại sau."}

async def generate(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    user_id = state.get("user_id")
    if not user_id:
        return {"generation": "Vui lòng đăng nhập để sử dụng tính năng này."}
    user_context = await memory_manager.get_user_preferences(user_id)
    if state.get("file_data"):
        documents.append(f"[Tài liệu Cá nhân Đính kèm]\n{state['file_data'][:6000]}")
    
    citation_instruction = "- Use inline source citations when referencing documents, e.g. [1], [2]." if documents else "- Do NOT use any citations as no relevant documents were found."
    thought_instruction = "- You MUST present your reasoning, analysis, and outline inside <think>...</think> tags at the beginning of your response, before delivering the final answer." if state.get("use_smart") else ""

    prompt = PromptTemplate(
        template="""SYSTEM IDENTITY: DocLib Core System - Answer Synthesis Engine.
OBJECTIVE: Synthesize a highly accurate, coherent, and professional response based on the provided reference documents.
OUTPUT_LANGUAGE: Must exactly match the language of the user's input query.

RULES:
- Base your answer strictly on the provided REFERENCE DOCUMENTS ({source_name}).
- If the documents do not contain the necessary information, state this clearly before attempting to answer based on general knowledge.
{citation_instruction}
{thought_instruction}
- Maintain a professional and objective tone.

USER CONTEXT:
{user_context}

REFERENCE DOCUMENTS ({source_name}):
{documents}

USER QUERY: {question}
RESPONSE:""",
        input_variables=["question", "documents", "source_name", "user_context", "citation_instruction", "thought_instruction"]
    )
    try:
        response = await llm_generate.ainvoke(prompt.format(
            question=question, documents="\n\n".join(documents), source_name="Hệ thống" if state.get("current_source") == "db" else "Internet",
            user_context=user_context, citation_instruction=citation_instruction, thought_instruction=thought_instruction
        ))
        generation = response.content
        mem0_manager.add_memory([{"role": "user", "content": question}, {"role": "assistant", "content": generation}], user_id)
        return {"generation": generation}
    except Exception as e:
        logger.error(f"Generate error: {e}")
        return {"generation": "Hệ thống đang gặp sự cố, vui lòng thử lại sau."}

async def grade_generation(state: AgentState):
    documents = state.get("documents", [])
    generation = state["generation"]
    
    if not documents:
        return {"hallucination_pass": "yes"}
        
    try:
        from src.agents.reasoning import reasoning_agent
        docs_list = [{"text": d, "metadata": {"title": "Nguồn"}} for d in documents]
        eval_res = await reasoning_agent.evaluate_quality(state["question"], generation, docs_list)
        
        is_hallucination = False
        if eval_res.get("should_retry") or eval_res.get("grounding", 1.0) < 0.6:
            is_hallucination = True
            
        if not is_hallucination and nli_model:
            docs_str = "".join(documents)[:1500]
            scores = await asyncio.to_thread(nli_model.predict, [[docs_str, generation]])
            if scores[0][0] > scores[0][1]:
                is_hallucination = True
                
        return {"hallucination_pass": "no" if is_hallucination else "yes"}
    except Exception as e:
        logger.error(f"Grade generation error: {e}")
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
knowledge_agent_app = workflow.compile()