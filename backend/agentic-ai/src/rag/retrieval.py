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
        try:
            from sentence_transformers import CrossEncoder
            self.reranker = CrossEncoder(settings.RERANKER_MODEL)
            logger.info(f"Loaded Reranker ({settings.RERANKER_MODEL}) successfully.")
        except Exception as e:
            self.reranker = None
            logger.error(f"Failed to load reranker: {e}")

    async def multi_query_retrieve(self, question: str, document_id: Optional[str] = None, k: int = 5) -> List[Dict]:
        logger.info(f"Multi-query retrieval for: {question}")
        
        prompt = PromptTemplate(
            template="""SYSTEM IDENTITY: DocLib Core System - Multi-Query Generator.
OBJECTIVE: Generate 3 alternative versions of the given question to improve vector search recall.
OUTPUT_LANGUAGE: Must exactly match the language of the original question.

RULES:
- Return ONLY a valid JSON array of strings. Do not include any explanations.
- Example: ["query 1", "query 2", "query 3"]

ORIGINAL QUESTION: {question}
OUTPUT:""",
            input_variables=["question"]
        )
        
        try:
            try:
                from pydantic import BaseModel, Field
                class MultiQueryOutput(BaseModel):
                    queries: List[str] = Field(description="List of 3 reformulated queries")
                
                structured_llm = self.llm.with_structured_output(MultiQueryOutput)
                response = structured_llm.invoke(prompt.format(question=question))
                queries = [q.strip() for q in response.queries if q.strip()]
            except Exception:
                import json
                import re
                response = self.llm.invoke(prompt.format(question=question))
                match = re.search(r'\[\s*".*"\s*\]', response.content, re.DOTALL)
                if match:
                    queries = json.loads(match.group(0))
                else:
                    queries = []
            
            queries = [q for q in queries if q]
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
        
        from src.rag.embedder import embedding_service
        query_vector = embedding_service.embed_query(query)
        
        fetch_limit = k * 3 if self.reranker else k
        
        docs = await vector_store.query(
            query_vector=query_vector,
            document_id=document_id,
            limit=fetch_limit
        )
        
        if not docs or not self.reranker:
            return docs[:k]
            
        try:
            pairs = [[query, doc.get("text", "")] for doc in docs]
            scores = self.reranker.predict(pairs)
            scored_docs = list(zip(docs, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            reranked_docs = [doc for doc, score in scored_docs]
            return reranked_docs[:k]
        except Exception as e:
            logger.error(f"Reranking error: {e}")
            return docs[:k]

retrieval_service = RetrievalService()