import asyncio
import json
import re
from typing import Dict, List, Optional

from langchain_core.prompts import PromptTemplate
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from loguru import logger
from src.core.registry import PromptType, registry
from src.store.vector import vector_store

from src.core.infrastructure.configuration import settings

_hf = HuggingFaceEndpoint(
    repo_id=settings.LLM_MODEL,
    huggingfacehub_api_token=settings.HF_TOKEN,
    temperature=0.1,
    task="conversational",
)
_llm = ChatHuggingFace(llm=_hf)

class RetrievalRag:
    """
    <module_purpose>
    <purpose>Handles advanced multi-dimensional and cross-document vector retrieval.</purpose>
    <metis_behavior>Employs Lost-in-the-Middle reordering and strict contextual bounds to eliminate hallucination vectors.</metis_behavior>
    </module_purpose>
    """
    def __init__(self):
        self.llm = _llm
        self._reranker = None

    @property
    def reranker(self):
        if self._reranker is None:
            try:
                from sentence_transformers import CrossEncoder

                self._reranker = CrossEncoder(settings.RERANKER_MODEL)
            except Exception as e:
                logger.exception("AI ranking model loading error")
                self._reranker = False
        return self._reranker

    def _extract_json_array(self, text: str) -> list:
        text = text.strip()
        text = re.sub(r"^```(?:json)?\n", "", text, flags=re.IGNORECASE | re.MULTILINE)
        text = re.sub(r"\n```$", "", text, flags=re.MULTILINE)
        match = re.search(r"\[[\s\S]*\]", text)
        if match:
            return json.loads(match.group(0))
        return []

    async def multi_query_retrieve(
        self, question: str, document_ids: Optional[List[str]] = None, k: int = 5
    ) -> List[Dict]:
        prompt = PromptTemplate(
            template=registry.get(PromptType.MULTI_QUERY),
            input_variables=["question"],
        )
        try:
            try:
                from pydantic import BaseModel, Field

                from src.schemas.routing import MultiQueryOutput

                structured_llm = self.llm.with_structured_output(MultiQueryOutput)
                response = structured_llm.invoke(prompt.format(question=question))
                queries = [q.strip() for q in response.queries if q.strip()]
            except Exception:
                response = self.llm.invoke(prompt.format(question=question))
                queries = self._extract_json_array(response.content)

            queries = [q for q in queries if q]
            queries.append(question)
        except Exception as e:
            logger.exception("Multi-dimensional query generation error")
            queries = [question]

        all_documents = []
        for q in queries:
            documents = await self.retrieve(q, document_ids, k=3)
            all_documents.extend(documents)

        seen_texts = set()
        unique_documents = []
        for d in all_documents:
            if d["text"] not in seen_texts:
                unique_documents.append(d)
                seen_texts.add(d["text"])

        return unique_documents[:k]

    async def retrieve(
        self, query: str, document_ids: Optional[List[str]] = None, k: int = 5
    ) -> List[Dict]:
        from src.rag.embedding import embedder

        query_vector = embedding.embed_query(query)

        current_reranker = self.reranker
        fetch_limit = k * 3 if current_reranker else k

        documents = await vector_store.query(
            query_vector=query_vector, document_ids=document_ids, limit=fetch_limit
        )

        if not documents or not current_reranker:
            return documents[:k]

        try:
            pairs = [[query, doc.get("text", "")] for doc in documents]
            scores = await asyncio.to_thread(current_reranker.predict, pairs)
            scored_documents = list(zip(documents, scores))
            scored_documents.sort(key=lambda x: x[1], reverse=True)
            reranked_documents = [doc for doc, score in scored_documents]
            return reranked_documents[:k]
        except Exception as e:
            logger.exception("Search result sorting error")
            return documents[:k]

    async def cross_document_retrieve(
        self, question: str, document_ids: List[str], k: int = 5
    ) -> List[Dict]:
        if not document_ids or len(document_ids) < 2:
            return await self.multi_query_retrieve(question, document_ids, k)

        decompose_prompt = (
            f"Given the question: {question}\n"
            f"There are {len(document_ids)} documents with IDs: {document_ids}\n"
            "For each document, generate one specific sub-query to retrieve the most relevant passage. "
            "Output as a JSON array of strings, one per document, in the same order"
        )

        sub_queries = [question] * len(document_ids)
        try:
            res = await asyncio.to_thread(self.llm.invoke, decompose_prompt)
            parsed = self._extract_json_array(res.content)
            if isinstance(parsed, list) and len(parsed) == len(document_ids):
                sub_queries = parsed
        except Exception as e:
            logger.exception("Cross-document query analysis error")

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

    def _lost_in_the_middle_reorder(self, documents: List[Dict]) -> List[Dict]:
        if len(documents) <= 2:
            return documents
        result = [None] * len(documents)
        left, right = 0, len(documents) - 1
        for i, doc in enumerate(documents):
            if i % 2 == 0:
                result[left] = doc
                left += 1
            else:
                result[right] = doc
                right -= 1
        return [d for d in result if d is not None]

retriever = RetrievalRag()
