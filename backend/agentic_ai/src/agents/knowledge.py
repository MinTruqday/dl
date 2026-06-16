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
                            res = await client.get(f"{settings.CONTENT_URL}/tai-lieu/{doc_id}", headers={"Authorization": f"Bearer {token}"}, timeout=settings.LONG_PROCESS_TIMEOUT)
                            if res.status_code == 200:
                                context_data += f"\nDocument {doc_id}:\n{res.json().get('data', {}).get('content', '')[:5000]}"
                    except Exception:
                        logger.warning("Mất kết nối mạng tạm thời")
                        
            prompt = prompt_registry.get(PromptType.MULTI_DOC_SYNTHESIS).format(query=query, context=context_data or "No specific documentation context available")
            result = await llm.ainvoke([HumanMessage(content=prompt)])
            logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
            return result.content
        except Exception:
            logger.error("Lỗi khi truy xuất tài liệu")
            return "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"

knowledge = KnowledgeAgent()