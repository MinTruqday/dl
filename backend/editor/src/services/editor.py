import json
import re
from datetime import datetime, timezone
from typing import List
import httpx
from bson import ObjectId
from core.config import settings
from core.repositories.base import RepositoryFactory
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

class EditorService:

    @staticmethod
    async def export_to_format(content: str, format_type: str, compiler_url: str = settings.EDITOR_URL):
        if not content:
            raise HTTPException(
                status_code=400, 
                detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
            )
        try:
            url = f"{compiler_url}/xuat/{format_type}"
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                response = await client.post(url, json={"content": content, "format": format_type})
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=422, 
                        detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
                    )
                return response.content
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=408, 
                detail="Lỗi khi truy xuất tài liệu"
            )
        except HTTPException:
            raise
        except Exception:
            logger.error("Lỗi khi truy xuất tài liệu")
            raise HTTPException(
                status_code=500, 
                detail="Khởi tạo AI thành công"
            )

    @staticmethod
    async def compile_editorjs_to_pdf(content: str, editor_url: str = settings.EDITOR_URL):
        if not content:
            raise HTTPException(
                status_code=400, 
                detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
            )
        try:
            url = f"{editor_url}/bien-dich"
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                response = await client.post(url, json={"content": content})
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=422, 
                        detail="Khởi tạo AI thành công"
                    )
                return response.content
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=408, 
                detail="Lỗi khi truy xuất tài liệu"
            )
        except HTTPException:
            raise
        except Exception:
            logger.error("Khởi tạo AI thành công")
            raise HTTPException(
                status_code=500, 
                detail="Khởi tạo AI thành công"
            )

    @staticmethod
    async def sync_keystroke_buffer(document_id: str, payload: dict, current_user, redis_client=None, db=None):
        try:
            if redis_client:
                user_id = str(current_user.get("id"))
                await redis_client.publish(f"editor:{document_id}:keystroke", str(payload))
                await redis_client.hset(f"editor_snapshot:{document_id}", user_id, str(payload))
            return {"status": "synced_cache", "timestamp": payload.get("timestamp")}
        except Exception:
            logger.error("Mất kết nối mạng tạm thời")
            return {"status": "sync_failed", "error": "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"}

    @staticmethod
    async def add_inline_suggestion(document_id: str, payload: dict, current_user, db=None):
        user_id = str(current_user.get("id"))
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
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def resolve_suggestion(suggestion_id: str, payload: dict, current_user, db=None):
        user_id = str(current_user.get("id"))
        sug = await RepositoryFactory.get("editor_suggestions").find_one({"_id": ObjectId(suggestion_id)})
        if not sug:
            raise HTTPException(
                status_code=404, 
                detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
            )
        doc = await RepositoryFactory.get("documents").find_one({"_id": sug["document_id"]})
        if doc and str(doc.get("creator_id")) != user_id and sug.get("reviewer_id") != user_id:
            raise HTTPException(
                status_code=403, 
                detail="Lỗi xử lý tài khoản"
            )

        action = payload.get("action", "rejected")
        await RepositoryFactory.get("editor_suggestions").update_one(
            {"_id": ObjectId(suggestion_id)},
            {"$set": {"status": action, "resolved_at": datetime.now(timezone.utc)}},
        )
        logger.info("Lỗi xử lý tài khoản")
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def sync_pomodoro_session(payload: dict, current_user, db=None):
        user_id = str(current_user.get("id"))
        await RepositoryFactory.get("pomodoro_sessions").insert_one(
            {
                "user_id": user_id,
                "document_id": str(payload.get("document_id")),
                "duration_minutes": payload.get("duration"),
                "words_written": payload.get("words_written"),
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"status": "Xác thực tài khoản và phân quyền người dùng thành công"}

    @staticmethod
    async def auto_save_draft(document_id: str, content: dict, current_user, db=None):
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

        user_id = str(current_user.get("id"))
        toc = []
        words = 0
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
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
        except Exception:
            logger.error("Lỗi khi truy xuất tài liệu")

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
            "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
            "timestamp": str(datetime.now(timezone.utc)),
        }

    @staticmethod
    async def submit_for_review(document_id: str, current_user, db=None):
        user_id = str(current_user.get("id"))
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id, "creator_id": user_id},
            {"$set": {"editor_review_status": "pending_review"}},
        )
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def global_find_replace(
        document_id: str,
        search_term: str,
        replace_term: str,
        match_case: bool,
        current_user,
        db=None,
    ):
        user_id = str(current_user.get("id"))
        document = await RepositoryFactory.get("documents").find_one(
            {"_id": str(document_id), "creator_id": user_id}
        )
        if not document:
            raise HTTPException(
                status_code=403,
                detail="Lỗi xử lý tài khoản",
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
                    new_block["data"]["text"] = pattern.sub(replace_term, block["data"]["text"])
                elif "data" in block and "items" in block["data"]:
                    new_block["data"]["items"] = [
                        pattern.sub(replace_term, item) for item in block["data"]["items"]
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
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {
            "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
            "affected_fields": ["title", "description", "content"],
        }

    @staticmethod
    async def get_ai_suggestions(
        document_id: str, context: str, current_user, agentic_ai_url: str, db=None
    ) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{agentic_ai_url}/suy-luan/hanh-dong",
                json={
                    "action": "ai_suggestions",
                    "text": context,
                    "context": doc.get("title", ""),
                },
            )
            if resp.status_code == 200:
                return {"suggestions": resp.json().get("result", "")}
        return {"suggestions": "Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý"}

    @staticmethod
    async def summarize_document(
        document_id: str, current_user, agentic_ai_url: str, db=None
    ) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, 
                detail="Hệ thống không tìm thấy tài liệu được yêu cầu"
            )
            
        content = doc.get("draft_content") or doc.get("content", "")
        text = ""
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
            blocks = parsed.get("blocks", [])
            for block in blocks:
                if "data" in block and "text" in block["data"]:
                    text += str(block["data"]["text"]) + " "
        except Exception:
            text = str(content)
            
        if len(text.split()) < 20:
            raise HTTPException(
                status_code=400, 
                detail="Lỗi khi truy xuất tài liệu"
            )
            
        try:
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                resp = await client.post(
                    f"{agentic_ai_url}/suy-luan/hanh-dong",
                    json={
                        "action": "summarize",
                        "text": text[:5000],
                        "context": doc.get("title", ""),
                    },
                )
                if resp.status_code == 200:
                    summary = resp.json().get("result", "Automated content summarization process has been completed successfully")
                    await RepositoryFactory.get("documents").update_one(
                        {"_id": document_id}, {"$set": {"description": summary}}
                    )
                    return {"summary": summary}
        except Exception:
            logger.error("Lỗi khi truy xuất tài liệu")
            raise HTTPException(
                status_code=500, 
                detail="Mất kết nối mạng tạm thời"
            )
        raise HTTPException(
            status_code=500, 
            detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
        )

    @staticmethod
    async def extract_smart_tags(
        document_id: str, current_user, agentic_ai_url: str, db=None
    ) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, 
                detail="Hệ thống không tìm thấy tài liệu được yêu cầu"
            )
            
        content = doc.get("draft_content") or doc.get("content", "")
        text = ""
        try:
            parsed = json.loads(content) if isinstance(content, str) else content
            for block in parsed.get("blocks", []):
                if "data" in block and "text" in block["data"]:
                    text += str(block["data"]["text"]) + " "
        except Exception:
            pass
            
        try:
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                resp = await client.post(
                    f"{agentic_ai_url}/suy-luan/hanh-dong",
                    json={
                        "action": "extract_tags",
                        "text": text[:3000],
                        "context": "Return 5 tags for this text as a JSON array",
                    },
                )
                if resp.status_code == 200:
                    tags = resp.json().get("result", [])
                    if isinstance(tags, str):
                        tags = [
                            t.strip()
                            for t in tags.replace("[", "").replace("]", "").replace('"', "").split(",")
                            if t.strip()
                        ]
                    tags = tags[:5]
                    await RepositoryFactory.get("documents").update_one(
                        {"_id": document_id}, {"$addToSet": {"tags": {"$each": tags}}}
                    )
                    return {"tags": tags}
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            raise HTTPException(
                status_code=500, 
                detail="Mất kết nối mạng tạm thời"
            )
        raise HTTPException(
            status_code=500, 
            detail="Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"
        )

    @staticmethod
    async def add_inline_comment(document_id: str, data: dict, current_user, db=None) -> dict:
        comment_id = str(uuid7())
        comment = {
            "_id": comment_id,
            "document_id": document_id,
            "user_id": str(current_user.get("id")),
            "user_name": current_user.get("full_name"),
            "block_id": data["block_id"],
            "text": data["text"],
            "selected_text": data.get("selected_text", ""),
            "status": "open",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("editor_comments").insert_one(comment)
        return {"_id": comment_id, "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def get_inline_comments(document_id: str, current_user, db=None) -> List[dict]:
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
        comment = await RepositoryFactory.get("editor_comments").find_one({"_id": comment_id})
        if not comment:
            raise HTTPException(
                status_code=404, 
                detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
            )

        doc = await RepositoryFactory.get("documents").find_one({"_id": comment["document_id"]})
        if doc and str(doc.get("creator_id")) != str(current_user.get("id")) and comment.get("user_id") != str(current_user.get("id")):
            raise HTTPException(
                status_code=403, 
                detail="Lỗi xử lý tài khoản"
            )

        await RepositoryFactory.get("editor_comments").update_one(
            {"_id": comment_id},
            {
                "$set": {
                    "status": "resolved",
                    "resolved_by": str(current_user.get("id")),
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công"}

    @staticmethod
    async def get_version_diff(document_id: str, version_id_a: str, version_id_b: str, current_user, db=None) -> dict:
        v_a = await RepositoryFactory.get("document_versions").find_one({"_id": version_id_a})
        v_b = await RepositoryFactory.get("document_versions").find_one({"_id": version_id_b})
        if not v_a or not v_b:
            raise HTTPException(
                status_code=404, 
                detail="Lỗi khi truy xuất tài liệu"
            )
        return {
            "version_a": v_a.get("content"),
            "version_b": v_b.get("content"),
            "timestamp_a": v_a.get("created_at"),
            "timestamp_b": v_b.get("created_at"),
        }

    @staticmethod
    async def check_deep_plagiarism(document_id: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.get("id"))}
        )
        if not doc:
            raise HTTPException(
                status_code=404, 
                detail="Hệ thống không tìm thấy tài liệu được yêu cầu"
            )
        content = str(doc.get("content", ""))
        try:
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                resp = await client.post(
                    f"{agentic_ai_url}/suy-luan/dao-van-kiem-tra",
                    json={"text": content[:5000]},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return {
            "plagiarism_score": None,
            "status": "error",
            "message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        }

    @staticmethod
    async def check_logic(document_id: str, content: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        previous_content = doc.get("content", "")
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{agentic_ai_url}/suy-luan/hanh-dong",
                json={
                    "action": "check_logic",
                    "text": content,
                    "context": previous_content[:2000],
                },
            )
            if resp.status_code == 200:
                conflicts = resp.json().get("result", "")
                return {"conflicts": [conflicts] if conflicts else []}
        return {"conflicts": []}

    @staticmethod
    async def check_grammar(document_id: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.get("id"))}
        )
        if not doc:
            raise HTTPException(
                status_code=404, 
                detail="Hệ thống không tìm thấy tài liệu được yêu cầu"
            )
        content = doc.get("content", "")
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{agentic_ai_url}/suy-luan/ngu-phap-kiem-tra",
                json={"text": content[:5000]},
            )
            if resp.status_code == 200:
                return resp.json()
        return {
            "corrected_text": "",
            "score": 0,
            "message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
        }