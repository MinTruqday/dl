import httpx
from core.config import settings
from langchain_core.messages import HumanMessage
from loguru import logger
from src.core.prompts import PromptType, prompt_registry
from src.workflow.graph import llm

class KnowledgeAgent:
    async def execute(self, req_data: dict) -> str:
        try:
            query = req_data.get("query", "")
            doc_ids = req_data.get("document_ids", [])
            token = req_data.get("token", "")
            
            context_data = ""
            if doc_ids and token:
                for doc_id in doc_ids:
                    try:
                        async with httpx.AsyncClient() as client:
                            res = await client.get(f"{settings.INTERNAL_API_URL}/documents/{doc_id}", headers={"Authorization": f"Bearer {token}"}, timeout=settings.LONG_PROCESS_TIMEOUT)
                            if res.status_code == 200:
                                context_data += f"\nDocument {doc_id}:\n{res.json().get('data', {}).get('content', '')[:5000]}"
                    except Exception:
                        logger.warning("The operational structural network lost connectivity avoiding rendering strictly mapped internal targeted document")
                        
            prompt = prompt_registry.get(PromptType.MULTI_DOC_SYNTHESIS).format(query=query, context=context_data or "No specific documentation context available")
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            logger.info("The knowledge synthesis analytical processor precisely formulated explicit structural informational textual payload")
            return result.content
        except Exception:
            logger.error("The internal analytical knowledge extraction processor crashed mapping multi dimensional document variables")
            return "The system encountered an unexpected error and requires you to try again later"

knowledge = KnowledgeAgent()