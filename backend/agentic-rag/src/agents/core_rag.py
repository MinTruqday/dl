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
from src.agents.retrieval_agent import retrieval_agent
from src.agents.memory_agent import memory_agent
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

class AgentState(TypedDict):
    chat_history: List[dict]
    question: str
    generation: str
    documents: List[str]
    retry_count: int
    hallucination_pass: str
    current_source: str
    route: str
    use_web: bool
    use_smart: bool
    user_id: str
    document_id: str
    image_data: str
    file_data: str

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
        template="""Bạn là một hệ thống thấu hiểu ngôn ngữ tự nhiên.
Dưới đây là lịch sử trò chuyện và câu nói mới nhất của người dùng.

Nhiệm vụ của bạn là trích xuất ý định thực sự của người dùng trong câu nói mới nhất thành một câu truy vấn độc lập, rõ ràng và trọn vẹn ý nghĩa.

Nguyên tắc hoạt động:
- Tự suy luận xem câu nói mới nhất đang nối tiếp chủ đề cũ hay đã chuyển sang chủ đề mới.
- Khôi phục mọi đại từ ẩn ý như nó, cái đó, ông ấy thành danh từ hoặc thực thể cụ thể dựa vào ngữ cảnh.
- Trả về duy nhất một câu truy vấn hoàn chỉnh đại diện cho ý định đó, không giải thích, không trò chuyện.

Lịch sử trò chuyện:
{history}

Câu nói mới nhất: {question}
Truy vấn hoàn chỉnh:""",
        input_variables=["history", "question"]
    )
    try:
        response = await llm.ainvoke(prompt.format(history=history_str, question=question))
        return {"question": response.content.strip()}
    except Exception as e:
        logger.error(f"Contextualization error: {e}")
        return {"question": question}

async def route_question(state: AgentState):
    question = state["question"]
    prompt = PromptTemplate(
        template="""Bạn là hệ thống Điều phối thông minh (Router). Nhiệm vụ của bạn là quyết định cách tốt nhất để phản hồi người dùng.

Câu hỏi của người dùng: "{question}"

Hãy đánh giá: Để trả lời câu hỏi này một cách chính xác nhất, bạn có cần tra cứu các tài liệu chuyên môn, dự án, quy trình hoặc dữ liệu bên ngoài không?

Nếu câu trả lời là có (câu hỏi về nội dung, tài liệu, dữ liệu cụ thể): Trả về 'rag'

Chỉ trả về duy nhất một từ ('rag' hoặc 'direct'), không kèm theo bất kỳ dấu câu hay lời giải thích nào khác.""",
        input_variables=["question"]
    )
    try:
        response = await llm.ainvoke(prompt.format(question=question))
        res = response.content.strip().lower()
        return {"current_source": "db", "route": "direct" if "direct" in res else "rag"}
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
        template="""Bạn là một Chuyên gia Chiến lược Tìm kiếm. Đứng trước câu hỏi: "{question}"

Bạn luôn áp dụng tư duy Đa Nhánh (Tree of Thoughts) để xử lý:
Thay vì nhảy vào tìm kiếm ngay, hãy ngầm đánh giá xem câu hỏi này chạm vào bao nhiêu khía cạnh nội dung khác nhau. Một câu hỏi đơn giản chỉ cần một nhánh duy nhất, trong khi một câu hỏi phức tạp thường ẩn chứa nhiều góc nhìn mà nếu tách ra sẽ giúp tìm kiếm hiệu quả hơn rất nhiều.

Nhiệm vụ của bạn:
- Nếu câu hỏi thuộc dạng tra cứu sự thật đơn giản (1 nhánh): Trả về đúng một từ "SIMPLE".
- Nếu câu hỏi phức tạp (nhiều nhánh): Đúc kết các nhánh suy nghĩ của bạn thành danh sách các câu truy vấn tối ưu nhất. In ra mỗi câu trên một dòng (tối đa 3 câu).

Chỉ trả về kết quả cuối cùng ("SIMPLE" hoặc danh sách truy vấn). Không in ra quá trình suy nghĩ.""",
        input_variables=["question"]
    )
    queries = [question]
    try:
        response = await llm.ainvoke(prompt.format(question=question))
        decision = response.content.strip()
        if "SIMPLE" not in decision.upper():
            for q in decision.split("\n"):
                q_clean = q.strip("- 123. ")
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
    from src.tools.web_search import web_search_tool
    question = state["question"]
    try:
        results = await web_search_tool.arun(question)
        return {"documents": [f"[Nguồn Internet]\n{results}"], "current_source": "internet"}
    except Exception as e:
        logger.error(f"Web search error: {e}")
        return {"documents": [], "current_source": "internet"}

async def grade_documents(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    prompt = PromptTemplate(
        template="""Bạn là Chuyên gia Thẩm định Dữ liệu. Hãy đánh giá: Tài liệu này có chứa thông tin giúp trả lời câu hỏi không?
Nếu có giá trị, trả về 'yes'. Nếu lạc đề, trả về 'no'.

Tài liệu: {context}
Câu hỏi: {question}
Kết luận:""",
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
        template="Viết lại câu hỏi để tối ưu tìm kiếm: {question}",
        input_variables=["question"]
    )
    try:
        res = await llm.ainvoke(prompt.format(question=question))
        return {"question": res.content.strip(), "retry_count": state.get("retry_count", 0) + 1, "current_source": "db"}
    except Exception as e:
        logger.error(f"Transform query error: {e}")
        return {"retry_count": state.get("retry_count", 0) + 1}

async def generate_direct(state: AgentState):
    prompt = f"Bạn là trợ lý DocLib thông thái. Trả lời người dùng thân thiện.\nCâu hỏi: {state['question']}"
    try:
        response = await llm_generate.ainvoke(prompt)
        return {"generation": response.content}
    except Exception as e:
        logger.error(f"Generate direct error: {e}")
        return {"generation": "Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu."}

async def generate(state: AgentState):
    question = state["question"]
    documents = state.get("documents", [])
    user_id = state.get("user_id")
    if not user_id:
        return {"generation": "Vui lòng đăng nhập để sử dụng tính năng này."}
    user_context = await memory_manager.get_user_preferences(user_id)
    if state.get("file_data"):
        documents.append(f"[Tài liệu Cá nhân Đính kèm]\n{state['file_data'][:6000]}")
    
    citation_instruction = "- Sử dụng trích dẫn nguồn inline (ví dụ: [1], [2])" if documents else "- Tuyệt đối KHÔNG sử dụng trích dẫn."
    thought_instruction = "- Trình bày lập luận trong thẻ <think>...</think>." if state.get("use_smart") else ""

    prompt = PromptTemplate(
        template="""Bạn là DocLib AI - Cố vấn thông thái. Hãy áp dụng quy trình tư duy sâu sau đây:

Quy trình tư duy nội bộ (không in ra ngoài):
1. Phân tích tài liệu: Quét toàn bộ nguồn cấp để lọc ra các bằng chứng xác đáng.
2. Kết nối logic: Xâu chuỗi các dữ kiện bằng tư duy phản biện.
3. Lập dàn ý: Sắp xếp các ý chính theo thứ tự ưu tiên.
4. Tổng hợp: Sinh câu trả lời cuối cùng dựa trên các bước trên.

Nguyên tắc phản hồi:
- Chỉ xuất ra kết quả cuối cùng từ bước 4. Tuyệt đối không in ra các tiêu đề "Bước 1, 2, 3".
- Sử dụng chữ viết thường và viết hoa đúng quy tắc tiếng Việt (Sentence case).
- Nếu tài liệu ({source_name}) KHÔNG có thông tin, hãy thông báo và có thể hỗ trợ bằng kiến thức hệ thống.
{citation_instruction}
{thought_instruction}
- Phản hồi bằng chính ngôn ngữ người dùng sử dụng.

Thông tin cá nhân hoá:
{user_context}

Dữ liệu tham khảo ({source_name}):
{documents}

Câu hỏi: {question}
Kết quả phản hồi (Chỉ in kết quả cuối cùng):""",
        input_variables=["question", "documents", "source_name", "user_context", "citation_instruction", "thought_instruction"]
    )
    try:
        response = await llm_generate.ainvoke(prompt.format(
            question=question, documents="\n\n".join(documents), source_name="Hệ thống" if state.get("current_source") == "db" else "Internet",
            user_context=user_context, citation_instruction=citation_instruction, thought_instruction=thought_instruction
        ))
        generation = response.content
        memory_agent.add_memory([{"role": "user", "content": question}, {"role": "assistant", "content": generation}], user_id)
        return {"generation": generation}
    except Exception as e:
        logger.error(f"Generate error: {e}")
        return {"generation": "Hệ thống gặp sự cố khi tổng hợp câu trả lời."}

async def grade_generation(state: AgentState):
    documents = state.get("documents", [])
    generation = state["generation"]
    if not documents or not nli_model:
        return {"hallucination_pass": "yes"}
    try:
        docs_str = "".join(documents)[:1500]
        scores = await asyncio.to_thread(nli_model.predict, [[docs_str, generation]])
        return {"hallucination_pass": "yes" if scores[0][1] > scores[0][0] else "no"}
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
rag_agent_app = workflow.compile()
