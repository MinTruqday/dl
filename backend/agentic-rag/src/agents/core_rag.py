import operator
from typing import Annotated, Sequence, TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
import os
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
import langchain
from langchain_huggingface import HuggingFaceEndpoint
from langchain_community.cache import RedisCache
from redis import Redis
from langchain_community.tools.tavily_search import TavilySearchResults
from loguru import logger
from src.store.vector_store import vector_store
from src.ingestion.embedder import embedding_service
from src.agents.retrieval_agent import retrieval_agent
from src.agents.memory_agent import memory_agent
from src.core.config import settings
from src.utils.file_processor import extract_text_from_base64

try:
    from sentence_transformers import CrossEncoder
    nli_model_name = settings.NLI_MODEL_NAME
    nli_model = CrossEncoder(nli_model_name)
    logger.info(f"Loaded NLI model: {nli_model_name}")
except Exception as e:
    nli_model = None
    logger.warning(f"Failed to load NLI model: {e}")

try:
    redis_url = settings.REDIS_URI
    langchain.llm_cache = RedisCache(redis_=Redis.from_url(redis_url))
except Exception as e:
    logger.warning(f"Failed to initialize RedisCache for Langchain: {e}")

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

llama_model = settings.LLAMA_MODEL
hf_token = settings.HF_TOKEN

from langchain_huggingface import ChatHuggingFace
_hf_endpoint = HuggingFaceEndpoint(
    repo_id=llama_model,
    huggingfacehub_api_token=hf_token,
    temperature=0.1,
    task="conversational",
    streaming=True
)
llm = ChatHuggingFace(llm=_hf_endpoint)
llm_generate = llm.with_config({"tags": ["final_generator"]})

try:
    embedder = embedding_service
except Exception as e:
    logger.error(f"Failed to initialize embedder: {e}")
    embedder = None

def contextualize_question(state: AgentState):
    logger.info("Contextualize question")
    question = state["question"]
    history = state.get("chat_history", [])
    
    if not history or len(history) == 0:
        return {"question": question, "chat_history": history}

    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-5:]])
    
    prompt = PromptTemplate(
        template="""Dựa vào Lịch sử trò chuyện và Câu hỏi mới nhất.
        Nhiệm vụ của bạn:
        1. Đánh giá xem Câu hỏi mới nhất có phụ thuộc ngữ cảnh không (ví dụ: chứa các đại từ 'nó', 'tài liệu đó', 'ông ấy', hoặc ý nghĩa bị khuyết thiếu).
        2. Nếu CÓ phụ thuộc: Viết lại câu hỏi kết hợp với chủ đề từ Lịch sử để nó trọn vẹn ngữ nghĩa.
        3. Nếu KHÔNG phụ thuộc (câu hỏi đã độc lập): PHẢI giữ nguyên và trả về chính xác Câu hỏi mới nhất.
        
        Tuyệt đối KHÔNG trả lời câu hỏi. Mọi phản hồi chỉ chứa một câu hỏi duy nhất (đã giữ nguyên hoặc viết lại).
        
        Lịch sử Chat:
        {history}
        
        Câu hỏi mới nhất: {question}
        Câu kết quả:""",
        input_variables=["history", "question"]
    )
    
    try:
        response = llm.invoke(prompt.format(history=history_str, question=question))
        new_q = response.content.strip()
        logger.info(f"Contextualized: {question} -> {new_q}")
        return {"question": new_q}
    except Exception as e:
        logger.error(f"Contextualization failed: {e}")
        return {"question": question}

def route_question(state: AgentState):
    logger.info("Route question")
    question = state["question"]
    prompt = PromptTemplate(
        template="Phân loại câu hỏi: Trả lời 'direct' nếu là câu giao tiếp xã giao thuần túy (xin chào, ai tạo ra bạn). Trả lời 'rag' nếu cần thông tin thực tế, kiến thức, nhân vật, tóm tắt tài liệu.\nCâu hỏi: {question}\nPhân loại:",
        input_variables=["question"]
    )
    try:
        response = llm.invoke(prompt.format(question=question))
        res = response.content.strip().lower()
        route = "direct" if "direct" in res else "rag"
    except Exception as e:
        logger.error(f"RAG Error: {e}")
        route = "rag"
    return {"current_source": "db", "route": route}

def decide_initial_route(state: AgentState):
    if state.get("route") == "direct": 
        return "generate_direct"
    return "preprocess_file"

def preprocess_file(state: AgentState):
    file_data = state.get("file_data")
    if file_data and file_data.startswith("data:"):
        logger.info("Processing uploaded file data")
        extracted_text = extract_text_from_base64(file_data)
        if extracted_text:
            return {"file_data": extracted_text}
    return {}

async def retrieve_db(state: AgentState):
    logger.info("RetrievalAgent: Retrieving from internal database")
    question = state["question"]
    document_id = state.get("document_id")
    documents = []

    if embedder:
        prompt = PromptTemplate(
            template="Bạn là ReasoningAgent. Câu hỏi gốc: {question}. Hãy lý luận và tạo ra 3 câu hỏi con (sub-queries) bằng tiếng Việt để quét đa góc độ. Chỉ trả về 3 câu, mỗi câu trên 1 dòng.",
            input_variables=["question"]
        )
        try:
            response = llm.invoke(prompt.format(question=question))
            sub_queries_res = response.content.strip()
            queries = [q.strip("- ") for q in sub_queries_res.split("\n") if q.strip()]
            queries.append(question)
        except Exception as e:
            logger.error(f"RAG Error: {e}")
            queries = [question]
            
        extracted_docs = []
        for q in queries[:4]: 
            results = await retrieval_agent.retrieve(query=q, document_id=document_id, k=3)
            for doc in results:
                chunk_id = doc.get("metadata", {}).get("chunk_id", "unknown")
                doc_name = doc.get("metadata", {}).get("title", "Tài liệu hệ thống")
                text = doc.get("text", "")
                formatted_doc = f"[Nguồn Tài liệu: {doc_name} | ID: {chunk_id}]\n{text}"
                extracted_docs.append(formatted_doc)
        documents = list(set(extracted_docs))
    return {"documents": documents, "question": question, "current_source": "db"}

def retrieve_internet(state: AgentState):
    logger.info("Retrieving from internet search")
    question = state["question"]
    documents = []
    try:
        tavily_tool = TavilySearchResults(max_results=3)
        docs = tavily_tool.invoke({"query": question})
        for d in docs:
            content = d.get("content", str(d))
            documents.append(f"[Nguồn Internet: Tavily Web Search]\n{content}")
    except Exception as e:
        logger.error(f"Tavily search error: {e}")
    return {"documents": documents, "current_source": "internet"}

def grade_documents(state: AgentState):
    logger.info(f"Grading documents from source: {state.get('current_source', 'unknown')}")
    question = state["question"]
    documents = state.get("documents", [])
    prompt = PromptTemplate(
        template="Tài liệu sau CÓ LIÊN QUAN hoặc chứa MỘT PHẦN thông tin hữu ích để trả lời cho câu hỏi không? Hãy nới lỏng tiêu chí: Nếu tài liệu đóng góp bất kỳ bằng chứng/manh mối nào để giải quyết câu hỏi thì trả lời `yes`. Chỉ trả lời `no` nếu tài liệu HOÀN TOÀN KHÔNG liên quan.\n\nTài liệu: {context}\n\nCâu hỏi: {question}\n\nĐánh giá (yes/no):",
        input_variables=["context", "question"]
    )
    filtered_docs = []
    for d in documents:
        try:
            response = llm.invoke(prompt.format(context=d, question=question))
            res = response.content.strip().lower()
            if "yes" in res:
                filtered_docs.append(d)
                logger.info("Document graded as: RELEVANT (yes)")
            else:
                logger.info("Document graded as: IRRELEVANT (no)")
        except Exception as e:
            logger.error(f"RAG Error: {e}")
            filtered_docs.append(d)
    return {"documents": filtered_docs}

def decide_after_grade(state: AgentState):
    if len(state.get("documents", [])) > 0:
        return "generate"
    current_source = state.get("current_source", "db")
    retry_count = state.get("retry_count", 0)
    use_web = state.get("use_web", False)
    if current_source == "db":
        if use_web:
            logger.info("Database empty. Falling back to internet search.")
            return "retrieve_internet"
        else:
            logger.info("Database empty. Web search disabled. Generating from knowledge base only.")
            return "generate"
    else:
        if retry_count < 2:
            logger.info("Internet search empty. Rewriting query.")
            return "transform_query"
        else:
            return "generate"

def transform_query(state: AgentState):
    logger.info("Rewriting query")
    question = state["question"]
    prompt = PromptTemplate(
        template="""Tạo 1 câu truy vấn khóa (keyword) ngắn gọn, sắc bén hơn để tìm kiếm tài liệu. 
        Ví dụ:
        - Câu hỏi cũ: Các mẹo để lập trình web tốt hơn là gì
        - Câu hỏi mới: Mẹo lập trình web hiệu quả
        - Câu hỏi cũ: Ai là người viết tác phẩm Tắt Đèn
        - Câu hỏi mới: Tác giả tác phẩm Tắt Đèn
        Câu hỏi cũ: {question}
        
        Câu hỏi mới:""",
        input_variables=["question"]
    )
    chain = prompt | llm
    response = chain.invoke({"question": question})
    new_question = response.content.strip()
    return {"question": new_question, "retry_count": state.get("retry_count", 0) + 1, "current_source": "db"}

async def generate_direct(state: AgentState):
    user_id = state.get("user_id", "guess_user")
    question = state["question"]
    user_context = memory_agent.get_context(question, user_id)
    prompt_str = f"Trò chuyện vui vẻ tự nhiên. Không cần tìm kiếm. \nThông tin cá nhân: {user_context}\nCâu hỏi: {question}"
    response = await llm_generate.ainvoke(prompt_str)
    generation = response.content
    if user_id != "guess_user":
        memory_agent.add_memory([
            {"role": "user", "content": question},
            {"role": "assistant", "content": generation}
        ], user_id)
    return {"generation": generation}

async def generate(state: AgentState):
    logger.info(f"Generating answer based on {state.get('current_source', 'Unknown').upper()}")
    question = state["question"]
    documents = state.get("documents", [])
    user_id = state.get("user_id", "guess_user")
    user_context = memory_agent.get_context(question, user_id)
    
    if state.get("file_data"):
        documents.append(f"[Tài liệu Cá nhân Đính kèm]\n{state['file_data']}")
        
    prompt = PromptTemplate(
        template="""Điều này rất quan trọng với dự án của tôi, xin hãy làm tốt nhất có thể!
        Bạn là một Chuyên gia Phân tích Tài liệu Học thuật túc trực tại hệ thống DocLib. 
        Dựa vào TÀI LIỆU bên dưới, hãy phân tích để trả lời CÂU HỎI. Nếu tài liệu không chứa đủ thông tin để trả lời, hãy trả lời chính xác là: 'Tôi không có đủ thông tin từ tài liệu để trả lời câu hỏi này'.
        
        Thông tin bộ nhớ cá nhân hoá:
        {user_context}
        
        ĐỊNH DẠNG TRẢ LỜI:
        - Tóm tắt ý chính ngay ở câu đầu tiên.
        - Trình bày chi tiết bằng các gạch đầu dòng rõ ràng.
        - Mọi thông tin sinh ra phải trích dẫn theo kiểu Inline Citation ngay tại câu (VD: 'Theo tài liệu [1] thì...').
        - NẾU người dùng yêu cầu xuất file, tạo bảng biểu để tải về, hoặc tạo file mã nguồn, HÃY bọc nội dung file đó trong một markdown code block với định dạng tương ứng (Ví dụ: ```csv\nid,name\n1,Test\n``` hoặc ```python\nprint("hello")\n```). Hệ thống sẽ tự động biến nó thành nút tải xuống cho người dùng. Kèm theo một vài lời giải thích ngắn gọn bên ngoài block.
        
        Bạn ĐANG đọc các tài liệu từ: {source_name}.
        
        Tài liệu:
        {documents}
        
        Câu hỏi: {question}
        Trả lời:""",
        input_variables=["question", "documents", "source_name", "user_context"]
    )
    source_name = "Kho tài liệu nội bộ (Độ tin cậy Tuyệt Đối)" if state.get("current_source") == "db" else "Internet (Độ tin cậy Tham Khảo)"
    docs_str = "\n\n".join(documents) if documents else ""
    
    formatted_prompt = prompt.format(question=question, documents=docs_str, source_name=source_name, user_context=user_context)
    
    if state.get("image_data"):
        content_blocks = [
            {"type": "text", "text": formatted_prompt},
            {"type": "image_url", "image_url": {"url": state["image_data"]}}
        ]
        messages = [HumanMessage(content=content_blocks)]
        try:
            response = await llm_generate.ainvoke(messages)
            generation = response.content
        except Exception as e:
            logger.error(f"Multimodal generation failed: {e}")
            response = await llm_generate.ainvoke(formatted_prompt)
            generation = response.content
    else:
        response = await llm_generate.ainvoke(formatted_prompt)
        generation = response.content
    
    if user_id != "guess_user":
        memory_agent.add_memory([
            {"role": "user", "content": question},
            {"role": "assistant", "content": generation}
        ], user_id)
    return {"generation": generation}

def grade_generation(state: AgentState):
    logger.info("Grading generation strictly via NLI")
    documents = state.get("documents", [])
    generation = state["generation"]
    if not documents or "Tôi không biết" in generation:
        return {"hallucination_pass": "yes"}
    docs_str = "".join(documents)
    if nli_model:
        try:
            scores = nli_model.predict([[docs_str[:1500], generation]]) 
            entail_score = scores[0][1]
            contradict_score = scores[0][0]
            logger.info(f"NLI Scores: Entail={entail_score:.2f}, Predict={contradict_score:.2f}")
            hallucination_pass = "yes" if entail_score > contradict_score else "no"
        except Exception as e:
            logger.error(f"NLI evaluation error: {e}")
            hallucination_pass = "yes"
    else:
        hallucination_pass = "yes"
    return {"hallucination_pass": hallucination_pass}

def check_hallucination(state: AgentState):
    if state.get("hallucination_pass", "yes") == "yes":
        logger.info("Generation passed hallucination check.")
        return END
    else:
        logger.info("Hallucination detected. Rewriting query to find better documents.")
        if state.get("retry_count", 0) > 2: return END
        return "transform_query"

def decide_after_retrieve(state: AgentState):
    if state.get("use_smart", False):
        return "grade_documents"
    else:
        docs = state.get("documents", [])
        if not docs and state.get("use_web", False) and state.get("current_source", "db") == "db":
            return "retrieve_internet"
        return "generate"

def decide_after_generate(state: AgentState):
    if state.get("use_smart", False):
        return "grade_generation"
    else:
        return END

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
workflow.add_conditional_edges("grade_documents", decide_after_grade, {"generate": "generate", "retrieve_internet": "retrieve_internet", "transform_query": "transform_query"})
workflow.add_edge("transform_query", "retrieve_db")
workflow.add_conditional_edges("generate", decide_after_generate, {"grade_generation": "grade_generation", END: END})
workflow.add_conditional_edges("grade_generation", check_hallucination, {"transform_query": "transform_query", END: END})

rag_agent_app = workflow.compile()
