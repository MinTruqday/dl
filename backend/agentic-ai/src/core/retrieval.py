from typing import List, Dict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
from loguru import logger
from src.core.config import settings
from src.store.vector_store import vector_store

from langchain_huggingface import ChatHuggingFace
_hf = HuggingFaceEndpoint(
    repo_id=settings.LLAMA_MODEL,
    huggingfacehub_api_token=settings.HF_TOKEN,
    temperature=0.1,
    task="conversational"
)
_llm = ChatHuggingFace(llm=_hf)

class RetrievalService:
    def __init__(self):
        self.llm = _llm

    async def multi_query_retrieve(self, question: str, document_id: Optional[str] = None, k: int = 5) -> List[Dict]:
        logger.info(f"Multi-query retrieval for: {question}")
        
        prompt = PromptTemplate(
            template="""SYSTEM IDENTITY: DocLib Core System - Multi-Query Generator.
OBJECTIVE: Generate 3 alternative versions of the given question to improve vector search recall.
OUTPUT_LANGUAGE: Must exactly match the language of the original question.

RULES:
- Output exactly 3 lines, each containing one reformulated query.
- Do NOT include any explanations or numbering.

ORIGINAL QUESTION: {question}
OUTPUT:""",
            input_variables=["question"]
        )
        
        try:
            response = self.llm.invoke(prompt.format(question=question))
            queries_text = response.content
            queries = [q.strip() for q in queries_text.split("\n") if q.strip()]
            queries.append(question)
        except Exception as e:
            logger.error(f"Multi-query generation error: {e}")
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
        logger.info(f"Retrieving for: {query} (document_id: {document_id})")
        
        from src.ingestion.embedder import embedding_service
        query_vector = embedding_service.embed_query(query)
        
        docs = vector_store.query(
            query_vector=query_vector,
            document_id=document_id,
            limit=k
        )
        
        return docs

retrieval_service = RetrievalService()