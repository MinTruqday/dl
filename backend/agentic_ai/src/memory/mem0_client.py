import os
from loguru import logger
from src.core.infrastructure.configuration import settings

class MemoryManager:
    def __init__(self):
        self.memory = None
        try:
            from mem0 import Memory
            config = {
                "vector_store": {
                    "provider": "qdrant",
                    "config": {
                        "host": settings.QDRANT_HOST,
                        "port": settings.QDRANT_PORT,
                    }
                }
            }
            # Fallback to default LLM (OpenAI) if HF is not natively supported by mem0 out of the box,
            # or rely on litellm. We will try default first.
            if os.getenv("OPENAI_API_KEY"):
                self.memory = Memory.from_config(config)
                logger.info("Mem0 memory initialized with Qdrant vector store.")
            else:
                logger.warning("Mem0 initialization skipped: OPENAI_API_KEY not found. Mem0 currently requires litellm/openai for extraction.")
        except ImportError:
            logger.warning("Mem0 library not installed. Skipping memory initialization.")
        except Exception as e:
            logger.error(f"Failed to initialize Mem0: {e}")

    async def add_memory(self, user_id: str, content: str, metadata: dict = None):
        """Add new context to long-term memory."""
        if not self.memory:
            return
        try:
            self.memory.add(content, user_id=user_id, metadata=metadata)
            logger.info(f"Added memory for user {user_id}")
        except Exception as e:
            logger.error(f"Error adding memory: {e}")

    async def get_memories(self, user_id: str, query: str = None) -> str:
        """Retrieve memories relevant to the current query."""
        if not self.memory:
            return ""
        try:
            if query:
                results = self.memory.search(query, user_id=user_id, limit=5)
            else:
                results = self.memory.get_all(user_id=user_id)
            
            if not results:
                return ""
                
            formatted = "\n".join([f"- {r['memory']}" for r in results if 'memory' in r])
            return f"Relevant Long-term Context:\n{formatted}\n"
        except Exception as e:
            logger.error(f"Error retrieving memory: {e}")
            return ""

mem0_manager = MemoryManager()
