import operator
import os
import langchain
from typing import Annotated, Sequence, TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_huggingface import HuggingFaceEndpoint, ChatHuggingFace
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
    logger.warning(f"Failed to initialize RedisCache: {e}")

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
    logger.info("Contextualizing question")
    question = state["question"]
    history = state.get("chat_history", [])
    
    if not history:
        return {"question": question, "chat_history": history}

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
        response = llm.invoke(prompt.format(history=history_str, question=question))
        new_q = response.content.strip()
        logger.info(f"Contextualized query: {new_q}")
        return {"question": new_q}
    except Exception as e:
        logger.error(f"Contextualization failed: {e}")
        return {"question": question}

def route_question(state: AgentState):
    logger.info("Routing question")
    question = state["question"]
    prompt = PromptTemplate(
        template="""Bạn là hệ thống Điều phối thông minh (Router). Nhiệm vụ của bạn là quyết định cách tốt nhất để phản hồi người dùng.

Câu hỏi của người dùng: "{question}"

Hãy đánh giá: Để trả lời câu hỏi này một cách chính xác nhất, bạn có cần tra cứu các tài liệu chuyên môn, dự án, quy trình hoặc dữ liệu bên ngoài không?

- Nếu câu trả lời là có (câu hỏi về kiến thức, tài liệu, dữ liệu cụ thể): Trả về 'rag'
- Nếu câu trả lời là không (giao tiếp chào hỏi, tâm sự, hoặc hỏi về bản thân AI): Trả về 'direct'

Chỉ trả về duy nhất một từ ('rag' hoặc 'direct'), không kèm theo bất kỳ dấu câu hay lời giải thích nào khác.""",
        input_variables=["question"]
    )
    try:
        response = llm.invoke(prompt.format(question=question))
        res = response.content.strip().lower()
        route = "direct" if "direct" in res else "rag"
    except Exception as e:
        logger.error(f"Routing error: {e}")
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
    logger.info("Retrieving from internal database")
    question = state["question"]
    document_id = state.get("document_id")
    documents = []

    if embedder:
        prompt = PromptTemplate(
            template="""Bạn là một Chuyên gia Chiến lược Tìm kiếm. Đứng trước câu hỏi: "{question}"

            Bạn luôn áp dụng tư duy Đa Nhánh (Tree of Thoughts) để xử lý:
            Thay vì nhảy vào tìm kiếm ngay, hãy ngầm đánh giá xem câu hỏi này chạm vào bao nhiêu khía cạnh tri thức khác nhau. Một câu hỏi đơn giản chỉ cần một nhánh duy nhất, trong khi một câu hỏi phức tạp thường ẩn chứa nhiều góc nhìn mà nếu tách ra sẽ giúp tìm kiếm hiệu quả hơn rất nhiều.

            Nhiệm vụ của bạn:
            - Nếu câu hỏi thuộc dạng tra cứu sự thật đơn giản (1 nhánh): Trả về đúng một từ "SIMPLE".
            - Nếu câu hỏi phức tạp (nhiều nhánh): Đúc kết các nhánh suy nghĩ của bạn thành danh sách các câu truy vấn tối ưu nhất. In ra mỗi câu trên một dòng (tối đa 3 câu).

            Chỉ trả về kết quả cuối cùng ("SIMPLE" hoặc danh sách truy vấn). Không in ra quá trình suy nghĩ.""",
            input_variables=["question"]
        )
        
        queries = [question]
        try:
            response = llm.invoke(prompt.format(question=question))
            decision = response.content.strip()
            if "SIMPLE" not in decision.upper():
                logger.info("Complex query detected. Adding sub-queries")
                for q in decision.split("\n"):
                    q_clean = q.strip("- 123. ")
                    if q_clean and q_clean.lower() != question.lower():
                        queries.append(q_clean)
        except Exception as e:
            logger.error(f"Retrieval strategy error: {e}")
            
        extracted_docs = []
        for q in list(dict.fromkeys(queries))[:4]: 
            results = await retrieval_agent.retrieve(query=q, document_id=document_id, k=3)
            for doc in results:
                chunk_id = doc.get("metadata", {}).get("chunk_id", "unknown")
                doc_name = doc.get("metadata", {}).get("title", "System Document")
                text = doc.get("text", "")
                formatted_doc = f"[Nguồn: {doc_name} | ID: {chunk_id}]\n{text}"
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
        logger.error(f"Internet search error: {e}")
    return {"documents": documents, "current_source": "internet"}

def grade_documents(state: AgentState):
    logger.info(f"Grading documents from source: {state.get('current_source', 'unknown')}")
    question = state["question"]
    documents = state.get("documents", [])
    prompt = PromptTemplate(
        template="""Bạn là Chuyên gia Thẩm định Dữ liệu. 
        Hãy đánh giá: Tài liệu này có chứa thông tin, manh mối hoặc bối cảnh nào giúp ích cho việc trả lời câu hỏi không?
        Nếu có giá trị tham khảo, trả về 'yes'. Nếu hoàn toàn lạc đề, trả về 'no'.
        
        Tài liệu: {context}
        Câu hỏi: {question}
        Kết luận (yes/no):""",
        input_variables=["context", "question"]
    )
    filtered_docs = []
    for d in documents:
        try:
            response = llm.invoke(prompt.format(context=d, question=question))
            res = response.content.strip().lower()
            if "yes" in res:
                filtered_docs.append(d)
                logger.info("Document relevant")
            else:
                logger.info("Document irrelevant")
        except Exception as e:
            logger.error(f"Grading error: {e}")
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
            logger.info("No relevant docs in DB. Falling back to internet")
            return "retrieve_internet"
        return "generate"
    else:
        if retry_count < 2:
            return "transform_query"
        return "generate"

def transform_query(state: AgentState):
    logger.info("Rewriting query")
    question = state["question"]
    prompt = PromptTemplate(
        template="""Bạn là Chuyên gia Khai thác Dữ liệu. Người dùng đã hỏi: "{question}" nhưng hệ thống chưa tìm được thông tin.
        Dựa trên bản năng của hệ thống tìm kiếm, hãy suy đoán xem người dùng thực sự đang tìm kiếm điều gì. 
        Loại bỏ các từ ngữ dư thừa, chuyển đổi câu hỏi thành một cụm từ khóa hoặc thuật ngữ chuyên môn có xác suất trúng đích cao nhất.
        
        Chỉ trả về duy nhất câu truy vấn mới đã được tối ưu hóa.""",
        input_variables=["question"]
    )
    chain = prompt | llm
    try:
        response = chain.invoke({"question": question})
        new_question = response.content.strip()
        logger.info(f"Transformed query: {new_question}")
        return {"question": new_question, "retry_count": state.get("retry_count", 0) + 1, "current_source": "db"}
    except Exception as e:
        logger.error(f"Transformation failed: {e}")
        return {"retry_count": state.get("retry_count", 0) + 1}

async def generate_direct(state: AgentState):
    user_id = state.get("user_id", "guess_user")
    question = state["question"]
    user_context = memory_agent.get_context(question, user_id)
    prompt_str = f"""Bạn là DocLib AI - một trợ lý thông minh và tinh tế.
    Nhiệm vụ của bạn là giao tiếp tự nhiên với người dùng. Dựa vào thông tin bạn biết về họ, hãy thể hiện sự thấu cảm và phản hồi như một cộng sự đắc lực. Hãy linh hoạt và thấu hiểu. Phản hồi bằng chính ngôn ngữ người dùng sử dụng.
    
    Thông tin người dùng: {user_context}
    Câu hỏi: {question}"""
    response = await llm_generate.ainvoke(prompt_str)
    generation = response.content
    if user_id != "guess_user":
        memory_agent.add_memory([
            {"role": "user", "content": question},
            {"role": "assistant", "content": generation}
        ], user_id)
    return {"generation": generation}

async def generate(state: AgentState):
    logger.info("Generating answer")
    question = state["question"]
    documents = state.get("documents", [])
    user_id = state.get("user_id", "guess_user")
    user_context = memory_agent.get_context(question, user_id)
    
    if state.get("file_data"):
        documents.append(f"[Tài liệu Cá nhân Đính kèm]\n{state['file_data']}")
        
    prompt = PromptTemplate(
        template="""Bạn là Cố vấn Thông thái của hệ thống DocLib. 
        Dựa trên nền tảng tài liệu được cung cấp, hãy phân tích để giải quyết trọn vẹn câu hỏi của người dùng.

        Quy trình tư duy:
        Bước 1: Quét tài liệu để trích xuất bằng chứng liên quan trực tiếp đến câu hỏi.
        Bước 2: Kết nối các bằng chứng bằng tư duy phản biện. Nếu tài liệu thiếu thông tin, hãy thông báo tôi không có đủ thông tin.
        Bước 3: Lập dàn ý ngầm (đi thẳng vào trọng tâm và cung cấp minh chứng).
        Bước 4: Sinh câu trả lời cuối cùng, linh hoạt sử dụng markdown như bảng biểu hoặc mã nguồn nếu cần thiết.

        Nguyên tắc cốt lõi:
        - Trích dẫn nguồn inline như [1], [2] khi tham khảo dữ kiện từ tài liệu.
        - Tự động phản hồi bằng chính ngôn ngữ của người dùng.
        - Tuyệt đối không tự bịa thông tin.

        Thông tin cá nhân hoá:
        {user_context}
        
        Nguồn tài liệu: {source_name}
        
        Tài liệu tham khảo:
        {documents}
        
        Câu hỏi người dùng: {question}
        Kết quả phản hồi:""",
        input_variables=["question", "documents", "source_name", "user_context"]
    )
    source_name = "Kho tài liệu nội bộ" if state.get("current_source") == "db" else "Internet"
    docs_str = "\n\n".join(documents) if documents else "Không có tài liệu tham khảo cụ thể."
    
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
            logger.error(f"Multimodal failed: {e}")
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
    logger.info("Grading generation via NLI")
    documents = state.get("documents", [])
    generation = state["generation"]
    if not documents or "không có đủ thông tin" in generation.lower():
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
        return END
    else:
        logger.info("Hallucination detected. Rewriting query")
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
