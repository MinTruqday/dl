class AIClient:
    async def inspect_knowledge_chunks(self, texts: list[str]) -> set[int]:
        from src.api.inference import inspect_knowledge_chunks
        from src.schemas.inference import KnowledgeChunkSafetyRequest

        payload = await inspect_knowledge_chunks(
            KnowledgeChunkSafetyRequest(texts=[text[:4000] for text in texts])
        )
        return {
            int(index)
            for index in payload.get("safe_indices", [])
            if isinstance(index, int) or str(index).isdigit()
        }

    async def summarize_knowledge_document(self, text: str) -> str:
        from src.api.inference import summarize_knowledge_document
        from src.schemas.inference import KnowledgeDocumentSummaryRequest

        payload = await summarize_knowledge_document(
            KnowledgeDocumentSummaryRequest(text=text[:15000])
        )
        return str(payload.get("summary") or "").strip()

    async def expand_retrieval_query(self, question: str) -> dict:
        from src.api.inference import expand_retrieval_query
        from src.schemas.inference import RetrievalExpansionRequest

        payload = await expand_retrieval_query(
            RetrievalExpansionRequest(question=question)
        )
        return {
            "hypothetical_document": str(
                payload.get("hypothetical_document") or question
            ),
            "queries": [
                str(query).strip()
                for query in payload.get("queries", [])
                if str(query).strip()
            ],
        }

    async def decompose_cross_document_query(
        self, question: str, document_ids: list[str]
    ) -> list[str]:
        from src.api.inference import decompose_cross_document_query
        from src.schemas.inference import CrossDocumentExpansionRequest

        payload = await decompose_cross_document_query(
            CrossDocumentExpansionRequest(
                question=question,
                document_ids=document_ids,
            )
        )
        return [
            str(query).strip()
            for query in payload.get("queries", [])
            if str(query).strip()
        ]


ai_client = AIClient()
