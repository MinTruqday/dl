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
    async def export_to_format(content: str, format_type: str, compiler_url: str = settings.COMPILER_URL):
        if not content:
            raise HTTPException(
                status_code=400, 
                detail="Requested operation cannot proceed because provided document content is completely empty"
            )
        try:
            url = f"{compiler_url}/export/{format_type}"
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                response = await client.post(url, json={"content": content, "format": format_type})
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=422, 
                        detail="System was unable to successfully export document to requested file format"
                    )
                return response.content
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=408, 
                detail="Document export process exceeded maximum allowed execution time and was terminated"
            )
        except HTTPException:
            raise
        except Exception:
            logger.error("Document export operation failed unexpectedly while processing the conversion request")
            raise HTTPException(
                status_code=500, 
                detail="Document export process encountered critical failure and could not be completed"
            )

    @staticmethod
    async def compile_editorjs_to_pdf(content: str, compiler_url: str = settings.COMPILER_URL):
        if not content:
            raise HTTPException(
                status_code=400, 
                detail="Requested operation cannot proceed because provided document content is completely empty"
            )
        try:
            url = f"{compiler_url}/compile"
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                response = await client.post(url, json={"content": content})
                if response.status_code != 200:
                    raise HTTPException(
                        status_code=422, 
                        detail="Document compilation process encountered critical failure and could not be completed"
                    )
                return response.content
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=408, 
                detail="Document compilation process exceeded maximum allowed execution time and was terminated"
            )
        except HTTPException:
            raise
        except Exception:
            logger.error("Background document compilation task failed to complete successfully")
            raise HTTPException(
                status_code=500, 
                detail="Document compilation process encountered critical failure and could not be completed"
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
            logger.error("Background task failed to synchronize editor keystroke buffer with remote cache")
            return {"status": "sync_failed", "error": "Synchronization process encountered unexpected system failure"}

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
        logger.info("New inline editorial suggestion has been successfully recorded for specified document")
        return {"message": "Inline editorial suggestion has been successfully submitted and saved"}

    @staticmethod
    async def resolve_suggestion(suggestion_id: str, payload: dict, current_user, db=None):
        user_id = str(current_user.get("id"))
        sug = await RepositoryFactory.get("editor_suggestions").find_one({"_id": ObjectId(suggestion_id)})
        if not sug:
            raise HTTPException(
                status_code=404, 
                detail="Requested editorial suggestion could not be located within the system records"
            )
        doc = await RepositoryFactory.get("documents").find_one({"_id": sug["document_id"]})
        if doc and str(doc.get("creator_id")) != user_id and sug.get("reviewer_id") != user_id:
            raise HTTPException(
                status_code=403, 
                detail="Current account lacks necessary permissions to resolve specific editorial suggestion"
            )

        action = payload.get("action", "rejected")
        await RepositoryFactory.get("editor_suggestions").update_one(
            {"_id": ObjectId(suggestion_id)},
            {"$set": {"status": action, "resolved_at": datetime.now(timezone.utc)}},
        )
        logger.info("Inline editorial suggestion has been marked as resolved by authorized account")
        return {"message": "Specified editorial suggestion has been successfully processed and updated"}

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
        logger.info("New focus session has been successfully recorded for the authenticated account")
        return {"status": "Session metrics have been successfully recorded"}

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
            logger.error("System encountered structural error attempting to parse document draft content")

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
            "message": "Current document draft has been successfully preserved in background storage",
            "timestamp": str(datetime.now(timezone.utc)),
        }

    @staticmethod
    async def submit_for_review(document_id: str, current_user, db=None):
        user_id = str(current_user.get("id"))
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id, "creator_id": user_id},
            {"$set": {"editor_review_status": "pending_review"}},
        )
        logger.info("Document has been successfully placed into editorial review queue by author")
        return {"message": "Specified document has been successfully queued for official editorial review"}

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
                detail="System could not locate specified document or account lacks access permissions",
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
        logger.info("Global search and replacement operation has been successfully executed on document")
        return {
            "message": "Global search and replacement operation has been successfully executed across document",
            "affected_fields": ["title", "description", "content"],
        }

    @staticmethod
    async def get_ai_suggestions(
        document_id: str, context: str, current_user, agentic_ai_url: str, db=None
    ) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{agentic_ai_url}/inference/actions",
                json={
                    "action": "ai_suggestions",
                    "text": context,
                    "context": doc.get("title", ""),
                },
            )
            if resp.status_code == 200:
                return {"suggestions": resp.json().get("result", "")}
        return {"suggestions": "Artificial intelligence service is currently unable to generate suggestions for content"}

    @staticmethod
    async def summarize_document(
        document_id: str, current_user, agentic_ai_url: str, db=None
    ) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, 
                detail="Requested document could not be located within the active system records"
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
                detail="Provided document does not contain enough text to generate meaningful summary"
            )
            
        try:
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                resp = await client.post(
                    f"{agentic_ai_url}/inference/actions",
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
            logger.error("Automated document summarization task encountered unexpected internal system failure")
            raise HTTPException(
                status_code=500, 
                detail="System unable to establish secure connection with artificial intelligence processing service"
            )
        raise HTTPException(
            status_code=500, 
            detail="Automated document summarization process could not be completed successfully"
        )

    @staticmethod
    async def extract_smart_tags(
        document_id: str, current_user, agentic_ai_url: str, db=None
    ) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, 
                detail="Requested document could not be located within the active system records"
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
                    f"{agentic_ai_url}/inference/actions",
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
            logger.error("Intelligent tag extraction process encountered unexpected internal system failure")
            raise HTTPException(
                status_code=500, 
                detail="System unable to establish secure connection with artificial intelligence processing service"
            )
        raise HTTPException(
            status_code=500, 
            detail="Intelligent contextual tags could not be successfully extracted from provided document"
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
        return {"_id": comment_id, "message": "Inline contextual comment has been successfully recorded and attached"}

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
                detail="Requested inline comment could not be located within the system records"
            )

        doc = await RepositoryFactory.get("documents").find_one({"_id": comment["document_id"]})
        if doc and str(doc.get("creator_id")) != str(current_user.get("id")) and comment.get("user_id") != str(current_user.get("id")):
            raise HTTPException(
                status_code=403, 
                detail="Current account lacks necessary authorization to mark specific comment as resolved"
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
        return {"message": "Selected inline comment has been successfully marked as resolved"}

    @staticmethod
    async def get_version_diff(document_id: str, version_id_a: str, version_id_b: str, current_user, db=None) -> dict:
        v_a = await RepositoryFactory.get("document_versions").find_one({"_id": version_id_a})
        v_b = await RepositoryFactory.get("document_versions").find_one({"_id": version_id_b})
        if not v_a or not v_b:
            raise HTTPException(
                status_code=404, 
                detail="System unable to locate specified document versions required for comparative analysis"
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
                detail="Requested document could not be located within the active system records"
            )
        content = str(doc.get("content", ""))
        try:
            async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
                resp = await client.post(
                    f"{agentic_ai_url}/inference/plagiarism-check",
                    json={"text": content[:5000]},
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            logger.error("Comprehensive originality analysis process encountered unexpected internal system failure")
        return {
            "plagiarism_score": None,
            "status": "error",
            "message": "Originality verification service is currently experiencing technical difficulties processing the request",
        }

    @staticmethod
    async def check_logic(document_id: str, content: str, current_user, agentic_ai_url: str, db=None) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        previous_content = doc.get("content", "")
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{agentic_ai_url}/inference/actions",
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
                detail="Requested document could not be located within the active system records"
            )
        content = doc.get("content", "")
        async with httpx.AsyncClient(timeout=settings.LONG_PROCESS_TIMEOUT) as client:
            resp = await client.post(
                f"{agentic_ai_url}/inference/grammar-check",
                json={"text": content[:5000]},
            )
            if resp.status_code == 200:
                return resp.json()
        return {
            "corrected_text": "",
            "score": 0,
            "message": "Grammatical analysis service is currently experiencing technical difficulties processing the request"
        }