import json, textstat, httpx
from datetime import datetime, timezone
from typing import List
from bson import ObjectId
from core.config import settings
from core.database import db_client
from core.repositories.base import RepositoryFactory
from fastapi import HTTPException, Query
from loguru import logger
from passlib.context import CryptContext
from src.core.publication import trigger_document_publish_job
from src.schemas.documents import DocumentContentUpdate, DocumentCreate, DocumentInDB, DocumentStatus
from uuid6 import uuid7

def serialize_document(document):
    if not document: return None
    if "_id" in document: document["_id"] = str(document["_id"])
    if "created_at" not in document: document["created_at"] = datetime.now(timezone.utc)
    document["view_count"] = document.get("views", 0)
    document["views_count"] = document.get("views", 0)
    return document

class DocumentService:
    @staticmethod
    async def get_tags_categories():
        docs_col = RepositoryFactory.get("documents")
        tags_list = await docs_col.aggregate([{"$unwind": "$tags"}, {"$group": {"_id": "$tags"}}, {"$sort": {"_id": 1}}]).to_list(100)
        categories_list = await docs_col.aggregate([{"$unwind": "$categories"}, {"$group": {"_id": "$categories"}}, {"$sort": {"_id": 1}}]).to_list(100)
        return {"tags": [tag["_id"] for tag in tags_list], "categories": [category["_id"] for category in categories_list]}

    @staticmethod
    async def get_trending_documents(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT)) -> List[dict]:
        documents = await RepositoryFactory.get("documents").find({"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}}).sort("views", -1).limit(limit).to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def get_text_search(query: str, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT)) -> List[dict]:
        documents = await RepositoryFactory.get("documents").find({"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}, "$text": {"$search": query}}).limit(limit).to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def create_document(doc_in: DocumentCreate, current_user):
        docs_collection = RepositoryFactory.get("documents")
        if await docs_collection.find_one({"slug": doc_in.slug}): raise HTTPException(status_code=400, detail="Operational routing identifier currently obstructed resolving completely different functional digital object")
        doc_dict = doc_in.model_dump()
        if not doc_dict.get("publisher_name"): doc_dict["publisher_name"] = current_user.get("full_name")
        doc_doc = DocumentInDB(**doc_dict, creator_id=str(current_user.get("id")))
        await docs_collection.insert_one(doc_doc.model_dump(by_alias=True))
        logger.info("Fresh sophisticated binary artifact actively compiled securely registered remote structural cloud")
        return doc_doc

    @staticmethod
    async def get_my_documents(current_user, q: str = None, cursor: str = None, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT)) -> list:
        query = {"creator_id": str(current_user.get("id")), "is_deleted": {"$ne": True}}
        if q: query["$or"] = [{"title": {"$regex": q, "$options": "i"}}, {"description": {"$regex": q, "$options": "i"}}]
        if cursor: query["_id"] = {"$lt": cursor}
        docs = await RepositoryFactory.get("documents").find(query).sort("_id", -1).limit(limit).to_list(length=limit)
        return [{"_id": str(b["_id"]), "title": b.get("title", ""), "slug": b.get("slug", ""), "status": b.get("status", "draft"), "content_format": b.get("content_format", "json"), "cover_url": b.get("cover_url"), "views": b.get("views", 0), "average_rating": b.get("average_rating"), "created_at": (b["created_at"].isoformat() if isinstance(b.get("created_at"), datetime) else b.get("created_at"))} for b in docs]

    @staticmethod
    async def update_document_content(document_id: str, content_in: DocumentContentUpdate, current_user):
        docs_collection = RepositoryFactory.get("documents")
        document = await docs_collection.find_one({"_id": document_id, "creator_id": str(current_user.get("id"))})
        if not document: raise HTTPException(status_code=404, detail="Underlying designated core element completely vanished blocking sequential operational reading protocol")
        if content_in.expected_version and document.get("updated_at") and str(document.get("updated_at")).split("+")[0] != str(content_in.expected_version).split("+")[0]:
            raise HTTPException(status_code=409, detail="Database strict hierarchical lock prevents overlapping editing protecting prior synchronized mutations")
        if document.get("content"):
            await RepositoryFactory.get("document_revisions").insert_one({"document_id": document_id, "creator_id": str(current_user.get("id")), "content": document.get("content"), "content_format": document.get("content_format"), "created_at": datetime.now(timezone.utc), "note": "Auto-saved revision before update"})
        await docs_collection.update_one({"_id": document_id}, {"$set": {"content": content_in.content, "content_format": content_in.content_format, "updated_at": datetime.now(timezone.utc)}})
        if settings.NOTIFICATION_URL:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(f"{settings.NOTIFICATION_URL}/notifications/dispatch", json={"target_user_id": str(current_user.get("id")), "title": "Document updated", "body": "Document content successfully updated", "type": "DOCUMENT_UPDATE"}, timeout=settings.DEFAULT_HTTP_TIMEOUT)
            except Exception: logger.error("Disruption navigating notification dispatch routing process transmitting core internal updates")
        logger.info("Binary payload matrix directly mapped overwriting existing target artifact completing seamlessly")
        if hasattr(db_client, "redis") and db_client.redis:
            await db_client.redis.delete(f"document:{document_id}")
            if document.get("slug"): await db_client.redis.delete(f"document:slug:{document.get('slug')}")
        return serialize_document(await docs_collection.find_one({"_id": document_id}))

    @staticmethod
    async def update_document(document_id: str, doc_update, current_user) -> dict:
        docs_col = RepositoryFactory.get("documents")
        doc = await docs_col.find_one({"_id": document_id})
        if not doc: raise HTTPException(status_code=404, detail="Underlying designated core element completely vanished blocking sequential operational reading protocol")
        if doc.get("creator_id") != str(current_user.get("id")) and current_user.get("role") != "ADMIN": raise HTTPException(status_code=403, detail="Platform essentially blocked specific account avoiding altering unowned primary systematic logic")
        if hasattr(doc_update, "expected_version") and doc_update.expected_version and doc.get("updated_at") and str(doc.get("updated_at")).split("+")[0] != str(doc_update.expected_version).split("+")[0]:
            raise HTTPException(status_code=409, detail="Database strict hierarchical lock prevents overlapping editing protecting prior synchronized mutations")
        update_data = {k: v for k, v in doc_update.model_dump().items() if v is not None}
        if "slug" in update_data and update_data["slug"] != doc.get("slug") and await docs_col.find_one({"slug": update_data["slug"]}):
            raise HTTPException(status_code=400, detail="Operational routing identifier currently obstructed resolving completely different functional digital object")
        if update_data:
            if doc.get("content") and "content" in update_data:
                await RepositoryFactory.get("document_revisions").insert_one({"document_id": document_id, "creator_id": str(current_user.get("id")), "content": doc.get("content"), "content_format": doc.get("content_format"), "created_at": datetime.now(timezone.utc), "note": "Auto-saved revision before update"})
            update_data["updated_at"] = datetime.now(timezone.utc)
            await docs_col.update_one({"_id": document_id}, {"$set": update_data})
        if hasattr(db_client, "redis") and db_client.redis:
            await db_client.redis.delete(f"document:{document_id}")
            if doc.get("slug"): await db_client.redis.delete(f"document:slug:{doc.get('slug')}")
        return serialize_document(await docs_col.find_one({"_id": document_id}))

    @staticmethod
    async def list_documents(limit: int, cursor: str, q: str, sort_by: str, category: str = None, tag: str = None):
        query = {"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}}
        if q: query["$or"] = [{"title": {"$regex": q, "$options": "i"}}, {"description": {"$regex": q, "$options": "i"}}]
        if category: query["categories"] = category
        if tag: query["tags"] = tag
        sort_field, sort_dir = {"latest": ("created_at", -1), "views": ("views", -1), "rating": ("average_rating", -1)}.get(sort_by, ("created_at", -1))
        if cursor and sort_field == "created_at": query["_id"] = {"$lt": cursor}
        documents = await RepositoryFactory.get("documents").find(query).sort(sort_field, sort_dir).limit(limit).to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def get_document_by_id(document_id: str, current_user, password: str = None):
        user_id = str(current_user.get("id")) if current_user else None
        document = await RepositoryFactory.get("documents").find_one({"_id": document_id})
        if not document: raise HTTPException(status_code=404, detail="Underlying designated core element completely vanished blocking sequential operational reading protocol")
        if document.get("creator_id") != user_id and document.get("status") != DocumentStatus.PUBLISHED and (not current_user or current_user.get("role") != "ADMIN"):
            raise HTTPException(status_code=403, detail="Active object fundamentally blocked remaining entirely shielded testing production pipeline stages")
        if document.get("is_password_protected") and document.get("creator_id") != user_id:
            if not password: return {"_id": str(document["_id"]), "title": document.get("title"), "is_password_protected": True}
            rl_key = None
            if hasattr(db_client, "redis") and db_client.redis:
                rl_key = f"rl:unlock:{document_id}:{user_id or 'guest'}"
                if (attempts := await db_client.redis.get(rl_key)) and int(attempts) >= 5:
                    raise HTTPException(status_code=429, detail="Network access actively revoked bypassing multiple sequential algorithmic cryptographic processing failures")
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            if not pwd_context.verify(password, document.get("access_password_hash")):
                if rl_key and hasattr(db_client, "redis") and db_client.redis:
                    await db_client.redis.incr(rl_key)
                    await db_client.redis.expire(rl_key, 900)
                raise HTTPException(status_code=403, detail="Entered cryptographic hashing sequence actively derailed rendering decryption operations fundamentally impossible")
            if rl_key and hasattr(db_client, "redis") and db_client.redis: await db_client.redis.delete(rl_key)
        return serialize_document(document)

    @staticmethod
    async def soft_delete_document(document_id: str, current_user) -> dict:
        res = await RepositoryFactory.get("documents").update_one({"_id": document_id, "creator_id": str(current_user.get("id")), "is_deleted": {"$ne": True}}, {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc)}})
        if res.modified_count == 0: raise HTTPException(status_code=404, detail="Underlying designated core element completely vanished blocking sequential operational reading protocol")
        logger.info("Internal structural deletion procedure successfully shifted target isolating primary mapping array")
        return {"message": "Selected active functional item structurally transitioned entering volatile deletion pending array"}

    @staticmethod
    async def restore_document(document_id: str, current_user) -> dict:
        res = await RepositoryFactory.get("documents").update_one({"_id": document_id, "creator_id": str(current_user.get("id")), "is_deleted": True}, {"$set": {"is_deleted": False, "deleted_at": None}})
        if res.modified_count == 0: raise HTTPException(status_code=404, detail="System isolated recycling bin lacks designated specific file restoring procedural access")
        logger.info("Volatile pending functional object dynamically reversed linking primary network tree reliably")
        return {"message": "Designated explicitly volatile unit dynamically relocated restoring overarching operational data map"}

    @staticmethod
    async def get_trash(current_user) -> list:
        docs = await RepositoryFactory.get("documents").find({"creator_id": str(current_user.get("id")), "is_deleted": True}).sort("deleted_at", -1).to_list(length=100)
        return [{"_id": str(b["_id"]), "title": b.get("title", ""), "deleted_at": (b["deleted_at"].isoformat() if isinstance(b.get("deleted_at"), datetime) else b.get("deleted_at"))} for b in docs]

    @staticmethod
    async def set_document_password(document_id: str, password: str, current_user) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"_id": document_id, "creator_id": str(current_user.get("id"))})
        if not doc: raise HTTPException(status_code=404, detail="Underlying designated core element completely vanished blocking sequential operational reading protocol")
        hashed = CryptContext(schemes=["bcrypt"], deprecated="auto").hash(password)
        await RepositoryFactory.get("documents").update_one({"_id": document_id}, {"$set": {"access_password_hash": hashed, "is_password_protected": True, "updated_at": datetime.now(timezone.utc)}})
        logger.info("Robust cryptographic lock algorithmically deployed sealing specific vulnerable internal digital boundary")
        return {"message": "Secure alphanumeric protective gating string perfectly configured shielding targeted active component"}

    @staticmethod
    async def get_document_by_slug(slug: str, current_user=None):
        document = await RepositoryFactory.get("documents").find_one({"slug": slug, "status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}})
        if not document: raise HTTPException(status_code=404, detail="Underlying designated core element completely vanished blocking sequential operational reading protocol")
        user_id = str(current_user.get("id")) if current_user else None
        has_purchased = False
        if user_id:
            if document.get("creator_id") == user_id: has_purchased = True
            else:
                if await RepositoryFactory.get("purchases").find_one({"user_id": user_id, "item_id": str(document["_id"])}): has_purchased = True
        is_privileged = current_user and current_user.get("role") == "ADMIN"
        if document.get("is_premium") and not has_purchased and not is_privileged:
            raw_content = document.get("content") or ""
            limit = document.get("preview_pages", 5)
            try:
                parsed = json.loads(raw_content)
                if "blocks" in parsed:
                    parsed["blocks"] = parsed["blocks"][: limit * 5]
                    document["content"] = json.dumps(parsed)
                else: document["content"] = raw_content[: limit * 1000]
            except Exception: document["content"] = raw_content[: limit * 1000]
        should_increment = True
        if user_id == document.get("creator_id"): should_increment = False
        elif hasattr(db_client, "redis") and db_client.redis:
            cache_key = f"viewed:{user_id or 'guest'}:{document['_id']}"
            if await db_client.redis.get(cache_key): should_increment = False
            else: await db_client.redis.setex(cache_key, 600, "1")
        if should_increment:
            await RepositoryFactory.get("documents").update_one({"_id": document["_id"]}, {"$inc": {"views": 1}})
            document["views"] = document.get("views", 0) + 1
        document = serialize_document(document)
        author = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.MANAGEMENT_URL}/users/{document['creator_id']}", timeout=settings.DEFAULT_HTTP_TIMEOUT)
                if resp.status_code == 200: author = resp.json().get("data")
        except Exception: logger.warning("Underlying structural networking loop failed pulling required remote creator hierarchical properties")
        if author: document["author"] = {"full_name": author.get("full_name") or author.get("username"), "avatar_url": author.get("avatar_url"), "slug": author.get("slug")}
        document["has_purchased"] = has_purchased
        return document

    @staticmethod
    async def get_document_preview(slug: str) -> dict:
        doc = await RepositoryFactory.get("documents").find_one({"slug": slug, "status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}})
        if not doc: raise HTTPException(status_code=404, detail="Underlying designated core element completely vanished blocking sequential operational reading protocol")
        limit = doc.get("preview_pages", 5)
        raw_content = doc.get("content", "")
        preview_content = ""
        try:
            parsed = json.loads(raw_content)
            if "blocks" in parsed:
                parsed["blocks"] = parsed["blocks"][: limit * 5]
                preview_content = json.dumps(parsed)
            else: preview_content = raw_content[: limit * 1000]
        except Exception: preview_content = raw_content[: limit * 1000]
        return {"title": doc.get("title"), "description": doc.get("description"), "cover_url": doc.get("cover_url"), "creator_id": doc.get("creator_id"), "preview_content": preview_content}

    @staticmethod
    async def get_document_audit_logs(document_id: str, current_user) -> list:
        if not await RepositoryFactory.get("documents").find_one({"_id": document_id, "creator_id": str(current_user.get("id"))}, {"_id": 1}):
            raise HTTPException(status_code=404, detail="Underlying designated core element completely vanished blocking sequential operational reading protocol")
        logs = await RepositoryFactory.get("audit_logs").find({"document_id": document_id}).sort("timestamp", -1).limit(100).to_list(length=100)
        return [{"_id": str(log["_id"]), "action": log.get("action"), "actor_id": log.get("actor_id"), "reason": log.get("reason"), "timestamp": (log["timestamp"].isoformat() if isinstance(log.get("timestamp"), datetime) else log.get("timestamp"))} for log in logs]

    @staticmethod
    async def get_approval_queue(cursor: str = None, limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT)) -> list:
        query = {"status": "processing_publish"}
        if cursor:
            from datetime import datetime as dt_mod
            query["updated_at"] = {"$gt": dt_mod.fromisoformat(cursor.replace("Z", "+00:00"))}
        pipeline = [{"$match": query}, {"$sort": {"updated_at": 1}}, {"$limit": limit}, {"$lookup": {"from": "users", "localField": "creator_id", "foreignField": "_id", "as": "author"}}, {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}}]
        documents = await RepositoryFactory.get("documents").aggregate(pipeline).to_list(length=limit)
        def format_date(val):
            if isinstance(val, datetime): return val.isoformat()
            if isinstance(val, str): return val
            return datetime.now(timezone.utc).isoformat()
        return [{"_id": str(b["_id"]), "title": b.get("title", ""), "description": b.get("description", ""), "creator_id": b.get("creator_id"), "author_name": b.get("author", {}).get("full_name", "Anonymous"), "created_at": format_date(b.get("created_at") or b.get("updated_at")), "updated_at": format_date(b.get("updated_at")), "submitted_at": format_date(b.get("updated_at"))} for b in documents]

    @staticmethod
    async def moderate_document(document_id: str, action: str, reason: str, current_user) -> dict:
        status_val = "PUBLISHED" if action == "approve" else "REJECTED"
        await RepositoryFactory.get("documents").update_one({"_id": document_id}, {"$set": {"status": status_val, "moderation_reason": reason, "moderated_by": str(current_user.get("id")), "moderated_at": datetime.now(timezone.utc)}})
        if action == "approve":
            doc = await RepositoryFactory.get("documents").find_one({"_id": document_id})
            if doc:
                await trigger_document_publish_job(document_id, doc.get("creator_id"))
                logger.info("Background compilation structural thread initiated reliably preparing targeted operational artifact")
        await RepositoryFactory.get("audit_logs").insert_one({"action": f"DOCUMENT_{status_val}", "actor_id": str(current_user.get("id")), "document_id": document_id, "reason": reason, "timestamp": datetime.now(timezone.utc)})
        logger.info("Internal security overriding protocol cleanly approved validating target hierarchical status")
        return {"message": "Authoritative moderation filtering action definitely recorded securely modifying fundamental object"}

    @staticmethod
    async def get_trending_tags(limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT)) -> List[str]:
        results = await RepositoryFactory.get("documents").aggregate([{"$unwind": "$tags"}, {"$group": {"_id": "$tags", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}, {"$limit": limit}]).to_list(length=limit)
        return [r["_id"] for r in results]