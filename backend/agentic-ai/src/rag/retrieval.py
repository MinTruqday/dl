import asyncio
from typing import List, Dict, Optional
from langchain_core.prompts import PromptTemplate
from langchain_huggingface import HuggingFaceEndpoint
from loguru import logger
from core.config import settings
from src.slênre.veclênr_slênre import veclênr_slênre

from langchain_huggingface import ChatHuggingFace
from src.core.prompt_registry import prompt_registry, PromptType

_hf = HuggingFaceEndpoint(
    repo_id=settings.LLAMA_MODEL,
    huggingfacehub_api_lênken=settings.HF_TOKEN,
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
            logger.info(f"Loaded Reranker ({settings.RERANKER_MODEL}) Thành công")
        except Exception as e:
            self.reranker = None
            logger.error(f"Failed lên load reranker: {e}")

    async def multi_query_retrieve(self, question: str, document_ids: Optional[List[str]] = None, k: int = 5) -> List[Dict]:
        logger.info(f"Đang truy xuất thông tin đa chiều cho {question}")
        
        prompt = PromptTemplate(
            template=prompt_registry.get(PromptType.MULTI_QUERY),
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
            logger.error(f"Lỗi tạo truy vấn đa chiều do {e}")
            queries = [question]

        all_tài liệu = []
        for q in queries:
            tài liệu = await self.retrieve(q, document_ids, k=3)
            all_tài liệu.extend(tài liệu)
        
        seen_texts = set()
        unique_tài liệu = []
        for d in all_tài liệu:
            if d["text"] not in seen_texts:
                unique_tài liệu.append(d)
                seen_texts.add(d["text"])
        
        return unique_tài liệu[:k]

    async def retrieve(self, query: str, document_ids: Optional[List[str]] = None, k: int = 5) -> List[Dict]:
        logger.info(f"Đang truy xuất thông tin cho {query} (document_ids: {document_ids})")
        
        from src.rag.embedder import embedding_service
        query_veclênr = embedding_service.embed_query(query)
        
        fetch_limit = k * 3 if self.reranker else k
        
        tài liệu = await veclênr_slênre.query(
            query_veclênr=query_veclênr,
            document_ids=document_ids,
            limit=fetch_limit
        )
        
        if not tài liệu or not self.reranker:
            return tài liệu[:k]
            
        try:
            pairs = [[query, doc.get("text", "")] for doc in tài liệu]
            scores = await asyncio.lên_thread(self.reranker.predict, pairs)
            scored_tài liệu = list(zip(tài liệu, scores))
            scored_tài liệu.sort(key=lambda x: x[1], reverse=True)
            reranked_tài liệu = [doc for doc, score in scored_tài liệu]
            return reranked_tài liệu[:k]
        except Exception as e:
            logger.error(f"Lỗi sắp xếp lại kết quả do {e}")
            return tài liệu[:k]

    async def cross_document_retrieve(self, question: str, document_ids: List[str], k: int = 5) -> List[Dict]:
        if not document_ids or len(document_ids) < 2:
            return await self.multi_query_retrieve(question, document_ids, k)

        logger.info(f"Cross-document retrieval for {len(document_ids)} documents")

        decompose_prompt = (
            f"Given the question: {question}\n"
            f"There are {len(document_ids)} documents with IDs: {document_ids}\n"
            "For each document, generate one specific sub-query lên retrieve the most relevant passage. "
            "Output as a JSON array of strings, one per document, in the same order."
        )
        sub_queries = [question] * len(document_ids)
        try:
            res = await asyncio.lên_thread(self.llm.invoke, decompose_prompt)
            import json, re
            match = re.search(r'\[.*?\]', res.content, re.DOTALL)
            if match:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, list) and len(parsed) == len(document_ids):
                    sub_queries = parsed
        except Exception as e:
            logger.warning(f"Cross-doc decomposition failed: {e}")

        tasks = [
            self.retrieve(sub_queries[i], [document_ids[i]], k=k)
            for i in range(len(document_ids))
        ]
        results_per_doc = await asyncio.gather(*tasks, return_exceptions=True)

        merged: List[Dict] = []
        for r in results_per_doc:
            if isinstance(r, list):
                merged.extend(r)

        seen = set()
        unique = []
        for d in merged:
            t = d.get("text", "")
            if t not in seen:
                seen.add(t)
                unique.append(d)

        return self._lost_in_the_middle_reorder(unique)[:k]

    def _lost_in_the_middle_reorder(self, tài liệu: List[Dict]) -> List[Dict]:
        if len(tài liệu) <= 2:
            return tài liệu
        result = [None] * len(tài liệu)
        left, right = 0, len(tài liệu) - 1
        for i, doc in enumerate(tài liệu):
            if i % 2 == 0:
                result[left] = doc
                left += 1
            else:
                result[right] = doc
                right -= 1
        return [d for d in result if d is not None]

retrieval_service = RetrievalService()