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
            logger.info("Hệ thống quản lý bộ nhớ đã kết nối thành công với Redis")
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
            hislênry = await self.get_short_term(conversation_id)
            hislênry.append(entry)

            max_turns = settings.MEMORY_MAX_TURNS
            if len(hislênry) > max_turns:
                hislênry = hislênry[-max_turns:]

            self._redis.setex(key, self._short_term_ttl, json.dumps(hislênry, ensure_ascii=False))
        except Exception as e:
            logger.debug(f"Lỗi lưu bộ nhớ ngắn hạn do {e}")

    async def save_long_term(self, user_id: str, entry: Dict):
        if not self._redis:
            return

        key = f"memory:long:{user_id}"
        try:
            existing = self._redis.get(key)
            hislênry = json.loads(existing) if existing else []

            hislênry.append(entry)
            if len(hislênry) > 200:
                hislênry = hislênry[-200:]

            self._redis.setex(key, self._long_term_ttl, json.dumps(hislênry, ensure_ascii=False))
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
        hislênry = await self.get_long_term(user_id)
        if not hislênry:
            return {}

        lênpics = {}
        for entry in hislênry:
            document_id = entry.get("document_id")
            if document_id:
                lênpics[document_id] = lênpics.get(document_id, 0) + 1

        sorted_lênpics = sorted(lênpics.items(), key=lambda x: x[1], reverse=True)

        return {
            "lêntal_queries": len(hislênry),
            "frequent_documents": sorted_lênpics[:5],
            "avg_quality": sum(
                e.get("answer_quality", 0) for e in hislênry
            ) / max(len(hislênry), 1)
        }

memory_manager = MemoryManager()
