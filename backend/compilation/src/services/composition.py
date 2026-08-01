import copy
import json
import re
from datetime import datetime, timezone
from typing import List

from bson import ObjectId
from fastapi import HTTPException
import httpx
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.redis import redis
from src.core.logic_logger import log_logic_execution
from src.repositories.composition import CompositionRepository
from src.repositories.pomodoro import PomodoroRepository


class CompositionService:
    @staticmethod
    def is_admin(current_user):
        return getattr(current_user.role, "value", current_user.role) == "admin"

    @staticmethod
    async def get_document(document_id: str, current_user, edit: bool = False):
        user_id = str(current_user.id)
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.CONTENT_URL}/tai-lieu/noi-bo/truy-cap",
                json={
                    "document_id": document_id,
                    "user_id": user_id,
                    "edit": edit,
                    "is_admin": CompositionService.is_admin(current_user),
                },
                headers={"X-Internal-Token": settings.SECRET_KEY},
            )
        if response.status_code == 404:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu hoặc thiếu quyền truy cập")
        response.raise_for_status()
        return response.json()["data"]

    @staticmethod
    @log_logic_execution
    async def sync_keystroke_buffer(document_id: str, payload: dict, current_user, cache=None):
        await CompositionService.get_document(document_id, current_user, edit=True)
        user_id = str(current_user.id)
        serialized = json.dumps(payload, ensure_ascii=False)
        await redis.publish(f"editor:{document_id}:keystroke", serialized)
        await redis.setex(f"editor_snapshot:{document_id}:{user_id}", 3600, serialized)
        return {"status": "synced", "timestamp": payload.get("timestamp")}

    @staticmethod
    @log_logic_execution
    async def add_inline_suggestion(document_id: str, payload: dict, current_user):
        await CompositionService.get_document(document_id, current_user)
        suggestion_id = str(uuid7())
        await CompositionRepository.insert_suggestion(
            {
                "_id": suggestion_id,
                "document_id": document_id,
                "reviewer_id": str(current_user.id),
                "selected_text": payload["selected_text"],
                "suggested_text": payload["suggested_text"],
                "comment": payload.get("comment"),
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
            }
        )
        return {"_id": suggestion_id}

    @staticmethod
    @log_logic_execution
    async def resolve_suggestion(suggestion_id: str, payload: dict, current_user):
        suggestion = await CompositionRepository.find_suggestion({"_id": suggestion_id})
        if not suggestion:
            raise HTTPException(status_code=404, detail="Không tìm thấy đề xuất chỉnh sửa")
        document = await CompositionService.get_document(
            suggestion["document_id"],
            current_user,
        )
        user_id = str(current_user.id)
        if (
            str(document.get("creator_id")) != user_id
            and suggestion.get("reviewer_id") != user_id
            and not CompositionService.is_admin(current_user)
        ):
            raise HTTPException(status_code=403, detail="Không có quyền giải quyết đề xuất")
        result = await CompositionRepository.update_suggestion(
            {"_id": suggestion_id, "status": "pending"},
            {
                "$set": {
                    "status": payload["action"],
                    "resolved_by": user_id,
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count != 1:
            raise HTTPException(status_code=409, detail="Đề xuất đã được giải quyết")
        return {"status": payload["action"]}

    @staticmethod
    @log_logic_execution
    async def sync_pomodoro_session(payload: dict, current_user):
        await CompositionService.get_document(payload["document_id"], current_user)
        session_id = str(uuid7())
        await PomodoroRepository.insert_session(
            {
                "_id": session_id,
                "user_id": str(current_user.id),
                "document_id": payload["document_id"],
                "duration_minutes": payload["duration"],
                "words_written": payload["words_written"],
                "created_at": datetime.now(timezone.utc),
            }
        )
        return {"_id": session_id, "status": "recorded"}

    @staticmethod
    @log_logic_execution
    async def auto_save_draft(document_id: str, content: dict, current_user):
        document = await CompositionService.get_document(document_id, current_user, edit=True)
        serialized = json.dumps(content, ensure_ascii=False)
        if len(serialized.encode("utf-8")) > settings.MAX_COMPILE_INPUT_BYTES:
            raise HTTPException(status_code=413, detail="Bản nháp vượt quá kích thước cho phép")
        blocks = content.get("blocks", [])
        if not isinstance(blocks, list) or len(blocks) > 5000:
            raise HTTPException(status_code=422, detail="Cấu trúc bản nháp không hợp lệ")
        toc = []
        words = 0
        for block in blocks:
            if not isinstance(block, dict):
                continue
            data = block.get("data", {})
            if block.get("type") == "header":
                toc.append(
                    {
                        "id": block.get("id"),
                        "text": str(data.get("text", ""))[:1000],
                        "level": max(1, min(int(data.get("level", 1)), 6)),
                    }
                )
            words += len(str(data.get("text", "")).split())
        now = datetime.now(timezone.utc)
        result = await CompositionService.content_db().documents.update_one(
            {"_id": document["_id"]},
            {
                "$set": {
                    "draft_content": content,
                    "toc": toc,
                    "reading_time_minutes": max(1, (words + 199) // 200),
                    "updated_at": now,
                }
            },
        )
        if result.modified_count != 1:
            raise HTTPException(status_code=409, detail="Bản nháp không có thay đổi")
        return {"timestamp": now.isoformat()}

    @staticmethod
    @log_logic_execution
    async def submit_for_review(document_id: str, current_user):
        document = await CompositionService.get_document(document_id, current_user, edit=True)
        if (
            str(document.get("creator_id")) != str(current_user.id)
            and not CompositionService.is_admin(current_user)
        ):
            raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có thể gửi xét duyệt")
        result = await CompositionService.content_db().documents.update_one(
            {"_id": document_id, "status": {"$nin": ["pending_review", "published"]}},
            {"$set": {"status": "pending_review", "updated_at": datetime.now(timezone.utc)}},
        )
        if result.modified_count != 1:
            raise HTTPException(status_code=409, detail="Tài liệu không thể chuyển sang trạng thái xét duyệt")
        return {"status": "pending_review"}

    @staticmethod
    @log_logic_execution
    async def global_find_replace(
        document_id: str,
        search_term: str,
        replace_term: str,
        match_case: bool,
        current_user,
    ):
        document = await CompositionService.get_document(document_id, current_user, edit=True)
        if str(document.get("creator_id")) != str(current_user.id) and not CompositionService.is_admin(current_user):
            raise HTTPException(status_code=403, detail="Chỉ chủ sở hữu mới có thể thay đổi toàn cục")
        flags = 0 if match_case else re.IGNORECASE
        pattern = re.compile(re.escape(search_term), flags=flags)
        update = {
            "title": pattern.sub(replace_term, str(document.get("title", ""))),
            "description": pattern.sub(replace_term, str(document.get("description", ""))),
            "updated_at": datetime.now(timezone.utc),
        }
        source_content = document.get("content")
        if isinstance(source_content, dict):
            new_content = copy.deepcopy(source_content)
            for block in new_content.get("blocks", []):
                data = block.get("data", {})
                if isinstance(data.get("text"), str):
                    data["text"] = pattern.sub(replace_term, data["text"])
                if isinstance(data.get("items"), list):
                    data["items"] = [
                        pattern.sub(replace_term, item) if isinstance(item, str) else item
                        for item in data["items"]
                    ]
            update["content"] = new_content
        await CompositionService.content_db().document_versions.insert_one(
            {
                "_id": str(uuid7()),
                "document_id": document_id,
                "creator_id": str(current_user.id),
                "note": "Tìm và thay thế",
                "snapshot": {
                    "title": document.get("title"),
                    "description": document.get("description"),
                    "content": document.get("content"),
                    "cover_url": document.get("cover_url"),
                    "tags": document.get("tags", []),
                    "categories": document.get("categories", []),
                },
                "created_at": datetime.now(timezone.utc),
            }
        )
        await CompositionService.content_db().documents.update_one(
            {"_id": document_id},
            {"$set": update},
        )
        return {"affected_fields": list(update)}

    @staticmethod
    @log_logic_execution
    async def add_inline_comment(document_id: str, data: dict, current_user) -> dict:
        await CompositionService.get_document(document_id, current_user)
        comment_id = str(uuid7())
        await CompositionRepository.insert_comment(
            {
                "_id": comment_id,
                "document_id": document_id,
                "user_id": str(current_user.id),
                "user_name": current_user.full_name,
                "block_id": data["block_id"],
                "text": data["text"],
                "selected_text": data.get("selected_text", ""),
                "status": "open",
                "created_at": datetime.now(timezone.utc),
            }
        )
        return {"_id": comment_id}

    @staticmethod
    @log_logic_execution
    async def get_inline_comments(document_id: str, current_user) -> List[dict]:
        await CompositionService.get_document(document_id, current_user)
        comments = await CompositionRepository.find_comments(
            {"document_id": document_id, "status": "open"}
        ).sort("created_at", -1).execute()
        for comment in comments:
            comment["_id"] = str(comment["_id"])
            if isinstance(comment.get("created_at"), datetime):
                comment["created_at"] = comment["created_at"].isoformat()
        return comments

    @staticmethod
    @log_logic_execution
    async def resolve_comment(comment_id: str, current_user) -> dict:
        comment = await CompositionRepository.find_comment({"_id": comment_id})
        if not comment:
            raise HTTPException(status_code=404, detail="Không tìm thấy bình luận")
        document = await CompositionService.get_document(comment["document_id"], current_user)
        user_id = str(current_user.id)
        if (
            str(document.get("creator_id")) != user_id
            and comment.get("user_id") != user_id
            and not CompositionService.is_admin(current_user)
        ):
            raise HTTPException(status_code=403, detail="Không có quyền giải quyết bình luận")
        result = await CompositionRepository.update_comment(
            {"_id": comment_id, "status": "open"},
            {
                "$set": {
                    "status": "resolved",
                    "resolved_by": user_id,
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        if result.modified_count != 1:
            raise HTTPException(status_code=409, detail="Bình luận đã được giải quyết")
        return {"status": "resolved"}

    @staticmethod
    @log_logic_execution
    async def get_version_diff(
        document_id: str,
        version_id_a: str,
        version_id_b: str,
        current_user,
    ) -> dict:
        await CompositionService.get_document(document_id, current_user)
        ids = [version_id_a, version_id_b]
        object_ids = [ObjectId(value) for value in ids if ObjectId.is_valid(value)]
        versions = await CompositionService.content_db().document_versions.find(
            {
                "document_id": document_id,
                "_id": {"$in": ids + object_ids},
            }
        ).to_list(length=2)
        by_id = {str(version["_id"]): version for version in versions}
        if version_id_a not in by_id or version_id_b not in by_id:
            raise HTTPException(status_code=404, detail="Không tìm thấy đủ hai phiên bản")
        first = by_id[version_id_a]
        second = by_id[version_id_b]
        return {
            "version_a": first.get("snapshot", {}).get("content", first.get("content")),
            "version_b": second.get("snapshot", {}).get("content", second.get("content")),
            "timestamp_a": first.get("created_at"),
            "timestamp_b": second.get("created_at"),
        }
