import os
from typing import List, Dict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
from loguru import logger
from src.store.vector_store import vector_store
llama_model = os.environ.get("LLAMA_MODEL")
hf_token = os.environ.get("HF_TOKEN")
from langchain_huggingface import ChatHuggingFace
_hf = HuggingFaceEndpoint(
    repo_id=llama_model,
    huggingfacehub_api_token=hf_token,
    temperature=0.1,
    task="conversational"
)
_llm = ChatHuggingFace(llm=_hf)
class RetrievalAgent:
    def __init__(self):
        self.llm = _llm
    async def multi_query_retrieve(self, question: str, document_id: Optional[str] = None, k: int = 5) -> List[Dict]:
logger.info("Log message sanitized"))
        prompt = PromptTemplate(
            template="""Bạn là một trợ lý AI có nhiệm vụ tối ưu hóa việc tìm kiếm tài liệu. 
            Hãy tạo ra 3 phiên bản khác nhau của câu hỏi dưới đây để giúp tìm kiếm vector hiệu quả hơn.
            Câu hỏi gốc: {question}
            Trả lời bằng 3 dòng, mỗi dòng là một phiên bản câu hỏi. Không thêm bất kỳ lời giải thích nào.""",
            input_variables=["question"]
        )
        try:
            response = self.llm.invoke(prompt.format(question=question))
            queries_text = response.content
            queries = [q.strip() for q in queries_text.split("\n") if q.strip()]
            queries.append(question)
        except Exception as e:
logger.info("Log message sanitized"))
            queries = [question]
        all_docs = []
        for q in queries:
            docs = await self.retrieve(q, document_id, k=3)
            all_docs.extend(docs)
        seen_texts = set()
        unique_docs = []
        for d in all_docs:
            if d["text"] not in seen_texts:
                unique_docs.append(d)
                seen_texts.add(d["text"])
        return unique_docs[:k]
    async def retrieve(self, query: str, document_id: Optional[str] = None, k: int = 5) -> List[Dict]:
logger.info("Log message sanitized"))
        from src.ingestion.embedder import embedding_service
        query_vector = embedding_service.embed_query(query)
        docs = vector_store.query(
            query_vector=query_vector,
            document_id=document_id,
            limit=k
        )
        return docs
retrieval_agent = RetrievalAgent()
