import httpx

from src.core.infrastructure.configuration import settings


class AgenticClient:
    async def inspect_rag_chunks(self, texts: list[str]) -> set[int]:
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(
                f"{settings.AGENTIC_AI_URL}/suy-luan/noi-bo/kiem-tra-doan-rag",
                json={"texts": [text[:4000] for text in texts]},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        response.raise_for_status()
        payload = response.json()
        return {
            int(index)
            for index in payload.get("safe_indices", [])
            if isinstance(index, int) or str(index).isdigit()
        }

    async def summarize_rag_document(self, text: str) -> str:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{settings.AGENTIC_AI_URL}/suy-luan/noi-bo/tom-tat-tai-lieu-rag",
                json={"text": text[:15000]},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        response.raise_for_status()
        return str(response.json().get("summary") or "").strip()

    async def expand_retrieval_query(self, question: str) -> dict:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.AGENTIC_AI_URL}/suy-luan/noi-bo/mo-rong-truy-van",
                json={"question": question},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        response.raise_for_status()
        payload = response.json()
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
        self,
        question: str,
        document_ids: list[str],
    ) -> list[str]:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{settings.AGENTIC_AI_URL}/suy-luan/noi-bo/phan-ra-lien-tai-lieu",
                json={"question": question, "document_ids": document_ids},
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        response.raise_for_status()
        payload = response.json()
        return [
            str(query).strip()
            for query in payload.get("queries", [])
            if str(query).strip()
        ]


agentic_client = AgenticClient()
