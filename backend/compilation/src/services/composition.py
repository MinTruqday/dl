from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from src.core.infrastructure.http_client import http_client
from bson import ObjectId
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.repositories.composition import CompositionRepository
from src.repositories.pomodoro import PomodoroRepository

class CompositionService:

    @staticmethod
    @log_logic_execution
    async def export_to_format(
        content: str, format_type: str, compiler_url: str = settings.COMPILATION_URL
    ):
        if not content:
            raise HTTPException(
                status_code=400, detail="Hệ thống không thể xử lý yêu cầu với nội dung tài liệu rỗng"
            )
        try:
            url = f"{compiler_url}/export/{format_type}"
            if True:
                response = await http_client.post(
                    url, json={"content": content, "format": format_type}
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=422, detail="Quá trình xuất tài liệu sang định dạng yêu cầu gặp sự cố"
                    )
                return response.content
        except httpx.TimeoutException as e:
            raise HTTPException(status_code=408, detail="Quá trình xuất tài liệu vượt quá thời gian quy định")
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Failed to convert document to requested export format")
            raise HTTPException(status_code=500, detail="Quá trình xuất tài liệu gặp sự cố kỹ thuật")

    @staticmethod
    @log_logic_execution
    async def compile_editorjs_to_pdf(
        content: str, compiler_url: str = settings.COMPILATION_URL
    ):
        if not content:
            raise HTTPException(
                status_code=400, detail="Hệ thống không thể xử lý yêu cầu với nội dung tài liệu rỗng"
            )
        try:
            url = f"{compiler_url}/compile"
            if True:
                response = await http_client.post(url, json={"content": content})
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=422, detail="Hệ thống gặp sự cố trong quá trình biên dịch tài liệu"
                    )
                return response.content
        except httpx.TimeoutException as e:
            raise HTTPException(
                status_code=408,
                detail="Quá trình biên dịch vượt quá thời gian quy định và đã bị hủy bỏ",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.exception("Unexpected error occurred during Tectonic compilation")
            raise HTTPException(status_code=500, detail="Quá trình biên dịch tài liệu gặp sự cố không mong muốn")

    @staticmethod
    @log_logic_execution
    async def sync_keystroke_buffer(
        document_id: str, payload: dict, current_user, cache=None
    ):
        try:
            if cache:
                user_id = str(current_user.id)
                await cache.publish(
                    f"editor:{document_id}:keystroke", str(payload)
                )
                await cache.hset(
                    f"editor_snapshot:{document_id}", user_id, str(payload)
                )
            return {"status": "synced_cache", "timestamp": payload.get("timestamp")}
        except Exception as e:
            logger.exception("Failed to synchronize document keystroke buffer from cache")
            return {"status": "sync_failed", "error": "Quá trình đồng bộ hóa dữ liệu từ bộ nhớ đệm gặp sự cố"}

    @staticmethod
    @log_logic_execution
    async def add_inline_suggestion(
        document_id: str, payload: dict, current_user
    ):
        user_id = str(current_user.id)
        await CompositionRepository.insert_suggestion(
            {
                "document_id": str(document_id),
                "reviewer_id": user_id,
                "selected_text": payload.get("selected_text"),
                "suggested_text": payload.get("suggested_text"),
                "comment": payload.get("comment"),
                "status": "pending",
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info("New inline suggestion successfully registered")
        return {"message": "Thực hiện ghi nhận thông tin đề xuất chỉnh sửa thành công"}

    @staticmethod
    @log_logic_execution
    async def resolve_suggestion(
        suggestion_id: str, payload: dict, current_user
    ):
        user_id = str(current_user.id)
        sug = await CompositionRepository.find_suggestion(
            {"_id": ObjectId(suggestion_id)}
        )
        if not sug:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy dữ liệu đề xuất chỉnh sửa trên hệ thống"
            )
        doc = None
        try:
            if True:
                r = await http_client.get(
                    f"{settings.CONTENT_URL}/tai-lieu/{sug['document_id']}",
                )
                if r.status_code == 200:
                    doc = r.json().get("data")
        except Exception as e:
            logger.exception("Failed to fetch document metadata to verify authorization")
        if (
            doc
            and str(doc.get("creator_id")) != user_id
            and sug.get("reviewer_id") != user_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Tài khoản không có đủ thẩm quyền để giải quyết đề xuất chỉnh sửa này",
            )

        action = payload.get("action", "rejected")
        await CompositionRepository.update_suggestion(
            {"_id": ObjectId(suggestion_id)},
            {
                "$set": {
                    "status": action,
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Inline suggestion successfully resolved")
        return {"message": "Thực hiện xử lý đề xuất chỉnh sửa thành công"}

    @staticmethod
    @log_logic_execution
    async def sync_pomodoro_session(payload: dict, current_user):
        user_id = str(current_user.id)
        await PomodoroRepository.insert_session(
            {
                "user_id": user_id,
                "document_id": str(payload.get("document_id")),
                "duration_minutes": payload.get("duration"),
                "words_written": payload.get("words_written"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info("Pomodoro session metrics successfully recorded")
        return {"status": "The session metrics have been successfully recorded"}

    @staticmethod
    @log_logic_execution
    async def auto_save_draft(document_id: str, content: dict, current_user):
        import re

        if isinstance(content, str):
            content = re.sub(
                r"<(script|iframe|object|embed|applet|style|link|meta)(.*?)>(.*?)</\1>",
                "",
                content,
                flags=re.IGNORECASE | re.DOTALL,
            )
            content = re.sub(r" on\w+\s*=", " ", content, flags=re.IGNORECASE)
        elif isinstance(content, dict):
            content_str = json.dumps(content)
            content_str = re.sub(
                r"<(script|iframe|object|embed|applet|style|link|meta)(.*?)>(.*?)</\1>",
                "",
                content_str,
                flags=re.IGNORECASE | re.DOTALL,
            )
            content_str = re.sub(r" on\w+\s*=", " ", content_str, flags=re.IGNORECASE)
            content = json.loads(content_str)

        user_id = str(current_user.id)
        toc = []
        words = 0
        try:
            if isinstance(content, str):
                parsed = json.loads(content)
            else:
                parsed = content
            blocks = parsed.get("blocks", [])
            for block in blocks:
                if block.get("type") == "header":
                    toc.append(
                        {
                            "id": block.get("id"),
                            "text": block.get("data", {}).get("text", ""),
                            "level": block.get("data", {}).get("level", 1),
                        }
                    )
                if "data" in block and "text" in block["data"]:
                    words += len(str(block["data"]["text"]).split())
        except Exception as e:
            logger.exception("Document structure analysis failed during draft parsing")

        reading_time_minutes = max(1, words // 200)
        try:
            if True:
                await http_client.put(
                    f"{settings.CONTENT_URL}/tai-lieu/{document_id}/noi-dung",
                    json={
                        "draft_content": content,
                        "toc": toc,
                        "reading_time_minutes": reading_time_minutes,
                    },
                    headers={"X-User-Id": user_id},
                )
        except Exception as e:
            logger.exception("Failed to persist document draft to content management system")
        return {
            "message": "Thực hiện thao tác lưu tự động bản nháp thành công",
            "timestamp": str(datetime.now(timezone.utc)),
        }

    @staticmethod
    @log_logic_execution
    async def submit_for_review(document_id: str, current_user):
        user_id = str(current_user.id)
        try:
            if True:
                await http_client.post(
                    f"{settings.CONTENT_URL}/ban-nhap/{document_id}/kiem-duyet",
                    json={"action": "pending_review"},
                    headers={"X-User-Id": user_id},
                )
        except Exception as e:
            logger.exception("Failed to submit document for administrative review")
        logger.info("Document successfully transitioned to pending review status")
        return {"message": "Đưa tài liệu vào hàng đợi xét duyệt thành công"}

    @staticmethod
    @log_logic_execution
    async def global_find_replace(
        document_id: str,
        search_term: str,
        replace_term: str,
        match_case: bool,
        current_user,
    ):
        import re

        user_id = str(current_user.id)
        document = None
        try:
            if True:
                r = await http_client.get(
                    f"{settings.CONTENT_URL}/tai-lieu/{document_id}",
                )
                if r.status_code == 200:
                    document = r.json().get("data")
        except Exception as e:
            logger.exception("Failed to fetch document metadata from content management system")
        if not document or str(document.get("creator_id")) != user_id:
            raise HTTPException(
                status_code=403,
                detail="Không tìm thấy tài liệu hoặc tài khoản không có quyền truy cập",
            )

        flags = 0 if match_case else re.IGNORECASE
        pattern = re.compile(re.escape(search_term), flags=flags)
        new_title = pattern.sub(replace_term, document.get("title", ""))
        new_desc = pattern.sub(replace_term, document.get("description", ""))

        content = document.get("content")
        new_content = None
        if content and isinstance(content, dict) and ("blocks" in content):
            new_content = content.copy()
            new_blocks = []
            for block in content.get("blocks", []):
                new_block = block.copy()
                if "data" in block and "text" in block["data"]:
                    new_block["data"]["text"] = pattern.sub(
                        replace_term, block["data"]["text"]
                    )
                elif "data" in block and "items" in block["data"]:
                    new_block["data"]["items"] = [
                        pattern.sub(replace_term, item)
                        for item in block["data"]["items"]
                    ]
                new_blocks.append(new_block)
            new_content["blocks"] = new_blocks

        update_payload = {
            "title": new_title,
            "description": new_desc,
        }
        if new_content:
            update_payload["content"] = new_content
        try:
            if True:
                await http_client.put(
                    f"{settings.CONTENT_URL}/tai-lieu/{document_id}",
                    json=update_payload,
                    headers={"X-User-Id": user_id},
                )
                await http_client.post(
                    f"{settings.CONTENT_URL}/phien-ban/luu/{document_id}",
                    params={"version_note": f"Tìm và thay thế: '{search_term}' → '{replace_term}'"},
                    headers={"X-User-Id": user_id},
                )
        except Exception as e:
            logger.exception("Failed to persist updated document content after find and replace")
        
        logger.info("Global find and replace operation completed successfully")
        return {
            "message": "Thao tác tìm kiếm và thay thế thành công",
            "affected_fields": ["title", "description", "content"],
        }

    @staticmethod
    @log_logic_execution
    async def add_inline_comment(
        document_id: str, data: dict, current_user
    ) -> dict:
        comment_id = str(uuid7())
        comment = {
            "_id": comment_id,
            "document_id": document_id,
            "user_id": str(current_user.id),
            "user_name": current_user.full_name,
            "block_id": data["block_id"],
            "text": data["text"],
            "selected_text": data.get("selected_text", ""),
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await CompositionRepository.insert_comment(comment)
        return {"_id": comment_id, "message": "Thực hiện thêm mới bình luận theo ngữ cảnh thành công"}

    @staticmethod
    @log_logic_execution
    async def get_inline_comments(
        document_id: str, current_user
    ) -> List[dict]:
        cursor = (
            CompositionRepository
            .find_comments({"document_id": document_id, "status": "open"})
            .sort("created_at", -1)
        )
        comments = await cursor 
        for c in comments:
            c["_id"] = str(c.get("_id", ""))
            if isinstance(c.get("created_at"), datetime):
                c["created_at"] = c["created_at"].isoformat()
            elif not c.get("created_at"):
                c["created_at"] = datetime.now(timezone.utc).isoformat().isoformat()
        return comments

    @staticmethod
    @log_logic_execution
    async def resolve_comment(comment_id: str, current_user) -> dict:
        comment = await CompositionRepository.find_comment(
            {"_id": comment_id}
        )
        if not comment:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy dữ liệu bình luận trực tiếp trên hệ thống"
            )

        doc = None
        try:
            if True:
                r = await http_client.get(
                    f"{settings.CONTENT_URL}/tai-lieu/{comment['document_id']}",
                )
                if r.status_code == 200:
                    doc = r.json().get("data")
        except Exception as e:
            logger.exception("Failed to fetch document metadata to verify authorization")
        if (
            doc
            and str(doc.get("creator_id")) != str(current_user.id)
            and comment.get("user_id") != str(current_user.id)
        ):
            raise HTTPException(
                status_code=403, detail="Tài khoản không có đủ thẩm quyền để đánh dấu giải quyết bình luận này"
            )

        await CompositionRepository.update_comment(
            {"_id": comment_id},
            {
                "$set": {
                    "status": "resolved",
                    "resolved_by": str(current_user.id),
                    "resolved_at": datetime.now(timezone.utc).isoformat(),
                }
            },
        )
        return {"message": "Thực hiện đánh dấu giải quyết bình luận thành công"}

    @staticmethod
    @log_logic_execution
    async def get_version_diff(
        document_id: str, version_id_a: str, version_id_b: str, current_user
    ) -> dict:
        v_a, v_b = None, None
        try:
            if True:
                ra = await http_client.get(
                    f"{settings.CONTENT_URL}/phien-ban/tai-lieu/{document_id}",
                )
                if ra.status_code == 200:
                    versions = ra.json().get("data", [])
                    for v in versions:
                        if str(v.get("_id")) == version_id_a:
                            v_a = v
                        if str(v.get("_id")) == version_id_b:
                            v_b = v
        except Exception as e:
            logger.exception("Failed to retrieve document version history for comparison")
        if not v_a or not v_b:
            raise HTTPException(
                status_code=404, detail="Hệ thống không tìm thấy các phiên bản tài liệu yêu cầu để thực hiện so sánh"
            )
        return {
            "version_a": v_a.get("content"),
            "version_b": v_b.get("content"),
            "timestamp_a": v_a.get("created_at"),
            "timestamp_b": v_b.get("created_at"),
        }

