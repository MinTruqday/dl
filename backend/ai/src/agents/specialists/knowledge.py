from loguru import logger
from src.workflow.graph import knowledge_app


class KnowledgeAgent:
    """
    <module_purpose>
    Veriq Analysis Agent for parsing raw user requests and preparing them for execution.
    </module_purpose>
    <contract>
    - Precondition: Receives a raw request object (dict or object).
    - Postcondition: Extracts and sanitizes metadata fields prior to orchestration dispatch.
    - Error Handling: Employs safe attribute and key lookups.
    </contract>
    """

    async def execute(self, req) -> str:
        logger.info("Querying MongoDB")
        try:
            if isinstance(req, dict):
                query = req.get("query", "")
                user_id = req.get("user_id", "")
                document_ids = req.get("document_ids", [])
                use_smart = req.get("thinking", False) or req.get("use_smart", False)
                use_web = req.get("use_web", False) or req.get("useWeb", False)
                chat_history = req.get("chat_history", []) or req.get("conversation_history", [])
                file_data = req.get("file_data")
                image_data = req.get("image_data")
                audio_data = req.get("audio_data")
                user_preferences = req.get("user_preferences", "")
                mode_directive = req.get("mode_directive", "")
            else:
                query = getattr(req, "query", "")
                user_id = getattr(req, "user_id", "")
                document_ids = getattr(req, "document_ids", [])
                use_smart = getattr(req, "thinking", False) or getattr(req, "use_smart", False)
                use_web = getattr(req, "useWeb", False) or getattr(req, "use_web", False)
                chat_history = getattr(req, "conversation_history", []) or getattr(
                    req, "chat_history", []
                )
                file_data = getattr(req, "file_data", None)
                image_data = getattr(req, "image_data", None)
                audio_data = getattr(req, "audio_data", None)
                user_preferences = getattr(req, "user_preferences", "")
                mode_directive = getattr(req, "mode_directive", "")

            result = await knowledge_app.ainvoke(
                {
                    "question": query,
                    "user_id": user_id,
                    "document_ids": document_ids,
                    "use_smart": use_smart,
                    "use_web": use_web,
                    "chat_history": chat_history,
                    "file_data": file_data,
                    "image_data": image_data,
                    "audio_data": audio_data,
                    "user_preferences": user_preferences,
                    "mode_directive": mode_directive,
                }
            )
            generation = result.get("generation")
            if not generation:
                raise RuntimeError("knowledge_pipeline_returned_no_generation")
            return generation
        except Exception:
            logger.exception("Knowledge base access error")
            raise RuntimeError("knowledge_pipeline_failed")


researcher = KnowledgeAgent()
