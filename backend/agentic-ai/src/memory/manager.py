import json
from loguru import logger
from typing import Dict, List, Optional
from core.config import settings
from datetime import datetime, timezone
import redis

class MemoryManager:
    def __init__(self):
        redis_url = settings.REDIS_URI
        try:
            self._redis = redis.from_url(redis_url, decode_responses=True)
            self._redis.ping()
            logger.info("Hệ thống quản lý bộ nhớ đã kết nối hoàn tất với Redis")
        except Exception as e:
            logger.warning(f"Không thể sử dụng Redis cho bộ nhớ: {e}")
            self._redis = None

        self._short_term_ttl = 3600 * 2
        self._long_term_ttl = 86400 * 30

    async def get_short_term(self, conversation_id: str) -> List[Dict]:
        if not self._redis:
            return []

        key = f"memory:short:{conversation_id}"
        try:
            data = self._redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"Lỗi đọc bộ nhớ ngắn hạn do {e}")
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

            self._redis.setex(key, self._short_term_ttl, json.dumps(history, ensure_ascii=False))
        except Exception as e:
            logger.debug(f"Lỗi lưu bộ nhớ ngắn hạn do {e}")

    async def save_long_term(self, user_id: str, entry: Dict):
        if not self._redis:
            return

        key = f"memory:long:{user_id}"
        try:
            existing = self._redis.get(key)
            history = json.loads(existing) if existing else []

            history.append(entry)
            if len(history) > 200:
                history = history[-200:]

            self._redis.setex(key, self._long_term_ttl, json.dumps(history, ensure_ascii=False))
        except Exception as e:
            logger.debug(f"Lỗi lưu bộ nhớ dài hạn do {e}")

    async def get_long_term(self, user_id: str) -> List[Dict]:
        if not self._redis:
            return []

        key = f"memory:long:{user_id}"
        try:
            data = self._redis.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.debug(f"Lỗi đọc bộ nhớ dài hạn do {e}")
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
            "avg_quality": sum(
                e.get("answer_quality", 0) for e in history
            ) / max(len(history), 1)
        }

memory_manager = MemoryManager()
