from typing import Dict, List
from src.store.graph import graph_store
from src.schemas.graph import RelationItem, GraphExpandResponse

class GraphService:
    async def expand(self, document_ids: List[str], seed_query: str, limit: int = 20) -> GraphExpandResponse:
        records = await graph_store.expand(document_ids, seed_query, limit)
        relations = [
            RelationItem(
                source=r.get("source", ""),
                relation=r.get("relation", ""),
                target=r.get("target", ""),
                document_id=r.get("document_id", "")
            )
            for r in records
        ]
        lines = [
            f"{r.source} --[{r.relation}]--> {r.target}"
            for r in relations
        ]
        context = "Knowledge graph context:\n" + "\n".join(lines) if lines else ""
        return GraphExpandResponse(context=context, relations=relations)

    async def replace_document(self, document_id: str, relations: List[RelationItem]) -> None:
        rel_dicts = [r.model_dump() for r in relations]
        await graph_store.replace_document(document_id, rel_dicts)

    async def delete_document(self, document_id: str) -> None:
        await graph_store.delete_document(document_id)

graph_service = GraphService()
