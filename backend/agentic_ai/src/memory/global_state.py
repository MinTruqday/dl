from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient

from src.core.infrastructure.configuration import settings


class GlobalStateManager:
    """
    <module_purpose>
    <purpose>Manages persistent global memory across sessions for Metis using MongoDB.</purpose>
    <metis_behavior>Persists preferences, project context, and episodic summaries. Retrieves relevant past episodes via vector search to inject into new sessions.</metis_behavior>
    </module_purpose>
    """

    _client: Optional[AsyncIOMotorClient] = None

    def __init__(self):
        if GlobalStateManager._client is None:
            GlobalStateManager._client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = GlobalStateManager._client[settings.AGENTIC_AI_DB_NAME]
        self._prefs = db["global_preferences"]
        self._context = db["global_project_context"]
        self._episodes = db["episodic_memory"]

    async def update_preference(self, key: str, value: Any):
        await self._prefs.update_one(
            {"key": key},
            {"$set": {"key": key, "value": value, "updated_at": datetime.datetime.utcnow()}},
            upsert=True,
        )
        logger.info("Global preference synchronization completed successfully")

    async def get_preference(self, key: str, default: Any = None) -> Any:
        doc = await self._prefs.find_one({"key": key})
        return doc["value"] if doc else default

    async def update_project_context(self, project_id: str, context: Dict[str, Any]):
        await self._context.update_one(
            {"project_id": project_id},
            {
                "$set": {
                    "project_id": project_id,
                    "context": context,
                    "updated_at": datetime.datetime.utcnow(),
                }
            },
            upsert=True,
        )
        logger.info("Project context synchronization completed successfully")

    def get_project_context(self, project_id: str) -> Dict[str, Any]:
        return {}

    async def get_project_context_async(self, project_id: str) -> Dict[str, Any]:
        doc = await self._context.find_one({"project_id": project_id})
        return doc["context"] if doc else {}

    async def add_episodic_memory(self, session_id: str, summary: str, embedding: Optional[List[float]] = None):
        doc = {
            "session_id": session_id,
            "summary": summary,
            "created_at": datetime.datetime.utcnow(),
            "expires_at": datetime.datetime.utcnow() + datetime.timedelta(days=90),
        }
        if embedding:
            doc["embedding"] = embedding
        await self._episodes.insert_one(doc)
        logger.info("Episodic memory stored successfully")

    async def get_recent_episodes(self, k: int = 3) -> List[str]:
        cursor = self._episodes.find(
            {"expires_at": {"$gt": datetime.datetime.utcnow()}},
            {"summary": 1},
            sort=[("created_at", -1)],
            limit=k,
        )
        docs = await cursor.to_list(length=k)
        return [d["summary"] for d in docs]

    async def get_relevant_episodes(self, query_embedding: List[float], k: int = 3) -> List[str]:
        try:
            pipeline = [
                {
                    "$vectorSearch": {
                        "index": "episodic_vector_index",
                        "path": "embedding",
                        "queryVector": query_embedding,
                        "numCandidates": k * 10,
                        "limit": k,
                    }
                },
                {"$match": {"expires_at": {"$gt": datetime.datetime.utcnow()}}},
                {"$project": {"summary": 1}},
            ]
            cursor = self._episodes.aggregate(pipeline)
            docs = await cursor.to_list(length=k)
            return [d["summary"] for d in docs]
        except Exception:
            logger.exception("Episodic vector search failed, falling back to recent episodes")
            return await self.get_recent_episodes(k)

    def add_history_event(self, event: str):
        pass


global_state = GlobalStateManager()
