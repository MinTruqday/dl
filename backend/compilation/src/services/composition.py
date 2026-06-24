import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx
from bson import ObjectId
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from shared.infrastructure.configuration import settings
from shared.repositories.base_repository import RepositoryFactory


class CompositionService:

    @staticmethod
    async def export_to_format(
        content: str, format_type: str, compiler_url: str = settings.COMPILATION_URL
    ):
        if not content:
            raise HTTPException(
                status_code=400, detail="Không thể xử lý vì tài liệu rỗng"
            )
        try:
            url = f"{compiler_url}/export/{format_type}"
            async with httpx.AsyncClient(
                timeout=settings.LONG_PROCESS_TIMEOUT
            ) as client:
                response = await client.post(
                    url, json={"content": content, "format": format_type}
                )
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=422, detail="Lỗi xuất định dạng tài liệu"
                    )
                return response.content
        except httpx.TimeoutException as e:
            raise HTTPException(status_code=408, detail=f"Quá thời gian xuất tài liệu: {e}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Lỗi chuyển đổi khi xuất tài liệu: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi xuất tài liệu: {e}")

    @staticmethod
    async def compile_editorjs_to_pdf(
        content: str, compiler_url: str = settings.COMPILATION_URL
    ):
        if not content:
            raise HTTPException(
                status_code=400, detail="Không thể xử lý vì tài liệu rỗng"
            )
        try:
            url = f"{compiler_url}/compile"
            async with httpx.AsyncClient(
                timeout=settings.LONG_PROCESS_TIMEOUT
            ) as client:
                response = await client.post(url, json={"content": content})
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=422, detail="Lỗi biên dịch tài liệu"
                    )
                return response.content
        except httpx.TimeoutException as e:
            raise HTTPException(
                status_code=408,
                detail=f"Quá thời gian chờ, quá trình biên dịch tài liệu bị hủy: {e}",
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Lỗi quá trình biên dịch tài liệu: {e}")
            raise HTTPException(status_code=500, detail=f"Lỗi biên dịch tài liệu: {e}")

    @staticmethod
    async def sync_keystroke_buffer(
        document_id: str, payload: dict, current_user, cache=None, db=None
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
            logger.error(f"Lỗi đồng bộ hóa dữ liệu bộ nhớ đệm: {e}")
            return {"status": "sync_failed", "error": f"Lỗi đồng bộ hóa dữ liệu: {e}"}

    @staticmethod
    async def add_inline_suggestion(
        document_id: str, payload: dict, current_user, db=None
    ):
        user_id = str(current_user.id)
        await RepositoryFactory.get("editor_suggestions").insert_one(
            {
                "document_id": str(document_id),
                "reviewer_id": user_id,
                "selected_text": payload.get("selected_text"),
                "suggested_text": payload.get("suggested_text"),
                "comment": payload.get("comment"),
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info("Đã ghi nhận đề xuất chỉnh sửa mới")
        return {"message": "Đã gửi đề xuất chỉnh sửa"}

    @staticmethod
    async def resolve_suggestion(
        suggestion_id: str, payload: dict, current_user, db=None
    ):
        user_id = str(current_user.id)
        sug = await RepositoryFactory.get("editor_suggestions").find_one(
            {"_id": ObjectId(suggestion_id)}
        )
        if not sug:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy đề xuất chỉnh sửa"
            )
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": sug["document_id"]}
        )
        if (
            doc
            and str(doc.get("creator_id")) != user_id
            and sug.get("reviewer_id") != user_id
        ):
            raise HTTPException(
                status_code=403,
                detail="Không có quyền giải quyết đề xuất chỉnh sửa này",
            )

        action = payload.get("action", "rejected")
        await RepositoryFactory.get("editor_suggestions").update_one(
            {"_id": ObjectId(suggestion_id)},
            {
                "$set": {
                    "status": action,
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Đã giải quyết đề xuất chỉnh sửa")
        return {"message": "Cập nhật đề xuất chỉnh sửa thành công"}

    @staticmethod
    async def sync_pomodoro_session(payload: dict, current_user, db=None):
        user_id = str(current_user.id)
        await RepositoryFactory.get("pomodoro_sessions").insert_one(
            {
                "user_id": user_id,
                "document_id": str(payload.get("document_id")),
                "duration_minutes": payload.get("duration"),
                "words_written": payload.get("words_written"),
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info("Ghi nhận phiên tập trung thành công")
        return {"status": "The session metrics have been successfully recorded"}

    @staticmethod
    async def auto_save_draft(document_id: str, content: dict, current_user, db=None):
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
            logger.error(f"Lỗi cấu trúc khi phân tích bản nháp: {e}")

        reading_time_minutes = max(1, words // 200)
        await RepositoryFactory.get("documents").update_one(
            {
                "_id": document_id,
                "$or": [{"creator_id": user_id}, {"co_authors": user_id}],
            },
            {
                "$set": {
                    "draft_content": content,
                    "toc": toc,
                    "reading_time_minutes": reading_time_minutes,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return {
            "message": "Lưu bản nháp thành công",
            "timestamp": str(datetime.now(timezone.utc)),
        }

    @staticmethod
    async def submit_for_review(document_id: str, current_user, db=None):
        user_id = str(current_user.id)
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id, "creator_id": user_id},
            {"$set": {"editor_review_status": "pending_review"}},
        )
        logger.info("Đã chuyển tài liệu vào hàng đợi xét duyệt")
        return {"message": "Đã đưa tài liệu vào hàng đợi xét duyệt"}

    @staticmethod
    async def global_find_replace(
        document_id: str,
        search_term: str,
        replace_term: str,
        match_case: bool,
        current_user,
        db=None,
    ):
        import re

        user_id = str(current_user.id)
        document = await RepositoryFactory.get("documents").find_one(
            {"_id": str(document_id), "creator_id": user_id}
        )
        if not document:
            raise HTTPException(
                status_code=403,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
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

        update_data = {
            "title": new_title,
            "description": new_desc,
            "updated_at": datetime.now(timezone.utc),
        }
        if new_content:
            update_data["content"] = new_content
        await RepositoryFactory.get("documents").update_one(
            {"_id": str(document_id)}, {"$set": update_data}
        )
        await RepositoryFactory.get("document_versions").insert_one(
            {
                "document_id": str(document_id),
                "creator_id": user_id,
                "action": "GLOBAL_REPLACE",
                "details": f"Replaced '{search_term}' with '{replace_term}'",
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info("Tìm kiếm và thay thế thành công")
        return {
            "message": "Thao tác tìm kiếm và thay thế thành công",
            "affected_fields": ["title", "description", "content"],
        }



    @staticmethod
    async def add_inline_comment(
        document_id: str, data: dict, current_user, db=None
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
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("editor_comments").insert_one(comment)
        return {"_id": comment_id, "message": "Ghi nhận bình luận thành công"}

    @staticmethod
    async def get_inline_comments(
        document_id: str, current_user, db=None
    ) -> List[dict]:
        cursor = (
            RepositoryFactory.get("editor_comments")
            .find({"document_id": document_id, "status": "open"})
            .sort("created_at", -1)
        )
        comments = await cursor.to_list(length=100)
        for c in comments:
            c["_id"] = str(c.get("_id", ""))
            if isinstance(c.get("created_at"), datetime):
                c["created_at"] = c["created_at"].isoformat()
            elif not c.get("created_at"):
                c["created_at"] = datetime.now(timezone.utc).isoformat()
        return comments

    @staticmethod
    async def resolve_comment(comment_id: str, current_user, db=None) -> dict:
        comment = await RepositoryFactory.get("editor_comments").find_one(
            {"_id": comment_id}
        )
        if not comment:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy bình luận trực tiếp"
            )

        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": comment["document_id"]}
        )
        if (
            doc
            and str(doc.get("creator_id")) != str(current_user.id)
            and comment.get("user_id") != str(current_user.id)
        ):
            raise HTTPException(
                status_code=403, detail="Không có quyền giải quyết bình luận này"
            )

        await RepositoryFactory.get("editor_comments").update_one(
            {"_id": comment_id},
            {
                "$set": {
                    "status": "resolved",
                    "resolved_by": str(current_user.id),
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        return {"message": "Đã đánh dấu bình luận là đã giải quyết"}

    @staticmethod
    async def get_version_diff(
        document_id: str, version_id_a: str, version_id_b: str, current_user, db=None
    ) -> dict:
        v_a = await RepositoryFactory.get("document_versions").find_one(
            {"_id": version_id_a}
        )
        v_b = await RepositoryFactory.get("document_versions").find_one(
            {"_id": version_id_b}
        )
        if not v_a or not v_b:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy phiên bản tài liệu để so sánh"
            )
        return {
            "version_a": v_a.get("content"),
            "version_b": v_b.get("content"),
            "timestamp_a": v_a.get("created_at"),
            "timestamp_b": v_b.get("created_at"),
        }


