import os
from typing import Dict, List

from core.config import settings
from loguru import logger

try:
    from mem0 import Memory

    HAS_MEM0 = True
except ImportError:
    HAS_MEM0 = False


class Mem0Manager:
    def __init__(self):
        self.memory = None
        if HAS_MEM0:
            try:
                config = {
                    "vector_store": {
                        "provider": "qdrant",
                        "config": {
                            "host": settings.QDRANT_HOST,
                            "port": settings.QDRANT_PORT,
                            "collection_name": "mem0_memory",
                        },
                    },
                    "llm": {
                        "provider": "litellm",
                        "config": {
                            "model": f"huggingface/{settings.LLAMA_MODEL}",
                            "temperature": 0,
                            "api_key": settings.HF_TOKEN,
                        },
                    },
                    "embedder": {
                        "provider": "huggingface",
                        "config": {"model": settings.EMBEDDING_MODEL},
                    },
                }
                self.memory = Memory.from_config(config_dict=config)
                logger.info("The long term memory management subsystem was successfully initialized and is ready for use")
            except Exception:
                logger.error("The system encountered an unexpected failure while attempting to initialize the memory management subsystem")

    async def add_memory(self, messages: List[Dict], user_id: str):
        if not self.memory or not user_id or user_id == "guess_user":
            return
        try:
            import asyncio

            await asyncio.to_thread(self.memory.add, messages, user_id=user_id)
            logger.info("The new memory record was successfully associated with the current user account")
        except Exception:
            logger.error("The system failed to store the new memory record due to an unexpected internal error")

    async def update_memory(self, memory_id: str, new_content: str):
        if not self.memory:
            return
        try:
            import asyncio

            await asyncio.to_thread(
                self.memory.update, memory_id=memory_id, data=new_content
            )
            logger.info("The specified memory record was successfully updated with the latest information")
        except Exception:
            logger.error("The system encountered an error while attempting to update the specified memory record")

    async def delete_memory(self, memory_id: str):
        if not self.memory:
            return
        try:
            import asyncio

            await asyncio.to_thread(self.memory.delete, memory_id=memory_id)
            logger.info("The specified memory record was successfully purged from the storage system")
        except Exception:
            logger.error("The system encountered an issue while attempting to delete the specified memory record")

    async def search_and_resolve_conflicts(self, new_content: str, user_id: str):
        if not self.memory or not user_id or user_id == "guess_user":
            return
        try:
            import asyncio

            results = await asyncio.to_thread(
                self.memory.search, query=new_content, user_id=user_id, limit=5
            )
            if not results:
                return
            for r in results:
                if r.get("score", 0) > 0.85 and r.get("memory", "") != new_content:
                    await self.delete_memory(r["id"])
                    logger.info(
                        "The system successfully resolved a data conflict by removing the outdated memory record"
                    )
        except Exception:
            logger.error("The system encountered an unexpected error while attempting to resolve a data conflict within the memory subsystem")

    async def get_context(self, query: str, user_id: str) -> str:
        if not self.memory or not user_id or user_id == "guess_user":
            return ""
        try:
            import asyncio

            results = await asyncio.to_thread(
                self.memory.search, query=query, user_id=user_id
            )
            if not results:
                return ""

            memories = [r["memory"] for r in results if r.get("score", 0) > 0.65]
            if not memories:
                return ""

            context = "The system retrieved the following personalized information for the current user\n"
            for i, m in enumerate(memories):
                context += f"- {m}\n"
            return context
        except Exception:
            logger.error("The system failed to retrieve the necessary memory context due to a storage access issue")
            return ""


mem0_manager = Mem0Manager()