import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

import redis.asyncio as redis
from loguru import logger

from src.core.infrastructure.configuration import settings

class ManagementMemory:
    def __init__(self):
        redis_url = settings.REDIS_URI
        try:
            self._redis = redis.from_url(redis_url, decode_responses=True)
        except Exception as e:
            logger.exception(f"Lỗi kết nối bộ đệm: {e}")
            self._redis = None

        self._short_term_ttl = 3600 * 2
        self._long_term_ttl = 86400 * 30

    async def get_short_term(self, conversation_id: str) -> List[Dict]:
        if not self._redis:
            return []

        key = f"memory:short:{conversation_id}"
        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.exception(f"Lỗi đọc dữ liệu bộ nhớ: {e}")
        return []

    async def save_short_term(self, conversation_id: str, entry: Dict):
        if not self._redis:
            return

        key = f"memory:short:{conversation_id}"
        try:
            history = await self.get_short_term(conversation_id)
            history.append(entry)

            max_turns = settings.MEMORY_MAX_TURNS
            if len(history) > max_turns:
                history = history[-max_turns:]

            await self._redis.setex(
                key, self._short_term_ttl, json.dumps(history, ensure_ascii=False)
            )
        except Exception as e:
            logger.exception(f"Lỗi lưu dữ liệu bộ nhớ: {e}")

    async def save_long_term(self, user_id: str, entry: Dict):
        if not self._redis:
            return

        key = f"memory:long:{user_id}"
        try:
            existing = await self._redis.get(key)
            history = json.loads(existing) if existing else []

            history.append(entry)
            if len(history) > 200:
                history = history[-200:]

            await self._redis.setex(
                key, self._long_term_ttl, json.dumps(history, ensure_ascii=False)
            )
        except Exception as e:
            logger.exception(f"Lỗi lưu trữ dữ liệu: {e}")

    async def get_long_term(self, user_id: str) -> List[Dict]:
        if not self._redis:
            return []

        key = f"memory:long:{user_id}"
        try:
            data = await self._redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.exception(f"Lỗi truy xuất dữ liệu lưu trữ dài hạn: {e}")
        return []

    async def get_user_preferences(self, user_id: str) -> Dict:
        history = await self.get_long_term(user_id)
        if not history:
            return {}

        topics = {}
        for entry in history:
            document_id = entry.get("document_id")
            if document_id:
                topics[document_id] = topics.get(document_id, 0) + 1

        sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_queries": len(history),
            "frequent_documents": sorted_topics[:5],
            "avg_quality": sum(e.get("answer_quality", 0) for e in history)
            / max(len(history), 1),
        }

memory_manager = ManagementMemory()
