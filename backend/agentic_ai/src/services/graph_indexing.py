from langchain_core.messages import SystemMessage

from src.core.infrastructure.configuration import settings
from src.core.registry import PromptType, registry
from src.schemas.memory import ExtractedGraph
from src.services.rag_client import rag_client
from src.utils.huggingface import create_chat_model


class GraphIndexingService:
    async def index_document(
        self,
        document_id: str,
        text: str,
        requester_id: str,
        is_admin: bool = False,
    ) -> int:
        relations = []
        if text.strip():
            model = create_chat_model(settings.LLM_MODEL).with_structured_output(
                ExtractedGraph
            )
            prompt = registry.get(PromptType.GRAPHRAG_ENTITY_EXTRACTION).format(
                text=text[:8000]
            )
            result = await model.ainvoke([SystemMessage(content=prompt)])
            relations = [relation.model_dump() for relation in result.relations]
        await rag_client.replace_graph(
            document_id,
            relations,
            requester_id,
            is_admin,
        )
        return len(relations)


graph_indexing_service = GraphIndexingService()
