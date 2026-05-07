from typing import List, Any
from core.config import settings
import datetime
from datetime import datetime, timezone as dt
import os
import uuid
import io
import json
import zipfile
from bson import ObjectId
from fastapi import HTTPException, status
from core.database import db_client
from models.document import DocumentCreate, DocumentInDB, DocumentStatus, DocumentContentUpdate
from loguru import logger
from services.notification import NotificationService

def serialize_document(document):
    if not document:
        return None
    if "_id" in document:
        document["_id"] = str(document["_id"])
    if "created_at" not in document:
        document["created_at"] = datetime.datetime.now(timezone.utc)
    return document

class DocumentService:
    @staticmethod
    async def get_tags_categories():
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        pipeline_tags = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags"}},
            {"$sort": {"_id": 1}}
        ]
        pipeline_categories = [
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories"}},
            {"$sort": {"_id": 1}}
        ]
        tags_list = await docs_col.aggregate(pipeline_tags).to_list(100)
        categories_list = await docs_col.aggregate(pipeline_categories).to_list(100)
        return {
            "tags": [tag["_id"] for tag in tags_list],
            "categories": [category["_id"] for category in categories_list]
        }

    @staticmethod
    async def get_trending_documents(limit: int = 5) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        cursor = docs_col.find({"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}}).sort("views", -1).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def get_semantic_search(query: str, limit: int = 10) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        cursor = docs_col.find({
            "status": DocumentStatus.PUBLISHED, 
            "is_deleted": {"$ne": True},
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}}
            ]
        }).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def get_ai_recommendations(limit: int = 10) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        cursor = docs_col.find({"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}}).sort([("average_rating", -1), ("views", -1)]).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def create_document(doc_in: DocumentCreate, current_user):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        existing_slug = await docs_collection.find_one({"slug": doc_in.slug})
        if existing_slug:
            raise HTTPException(status_code=400, detail="Đường dẫn tài liệu này đã tồn tại.")
        
        doc_dict = doc_in.model_dump()
        if not doc_dict.get("publisher_name"):
            doc_dict["publisher_name"] = current_user.full_name

        doc_doc = DocumentInDB(**doc_dict, author_id=str(current_user.id))
        await docs_collection.insert_one(doc_doc.model_dump(by_alias=True))
        logger.info(f"Workspace: Document created {doc_doc.id} by author {current_user.id}")
        return doc_doc

    @staticmethod
    async def get_my_documents(current_user, skip: int = 0, limit: int = 50) -> list:
        db = db_client.mongodb.get_default_database()
        docs = await db["documents"].find(
            {"author_id": str(current_user.id), "is_deleted": {"$ne": True}}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
        return [
            {
                "id": str(b["_id"]),
                "title": b.get("title", ""),
                "slug": b.get("slug", ""),
                "status": b.get("status", "draft"),
                "cover_url": b.get("cover_url"),
                "views": b.get("views", 0),
                "average_rating": b.get("average_rating"),
                "chapters_count": len(b.get("chapters", [])),
                "created_at": b["created_at"].isoformat() if isinstance(b.get("created_at"), datetime.datetime) else b.get("created_at"),
            }
            for b in docs
        ]

    @staticmethod
    async def update_document_content(document_id: str, content_in: DocumentContentUpdate, current_user):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        document = await docs_collection.find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        await docs_collection.update_one(
            {"_id": document_id},
            {"$set": {
                "content": content_in.content, 
                "content_format": content_in.content_format,
                "updated_at": datetime.datetime.now(timezone.utc)
            }}
        )
        await NotificationService.notify_document_update(document_id, document.get("title", "Tài liệu"), current_user.full_name)
        logger.info(f"Workspace: Document content updated {document_id} by {current_user.id}")
        return await docs_collection.find_one({"_id": document_id})

    @staticmethod
    async def list_documents(limit: int, offset: int, q: str, sort_by: str, category: str = None, tag: str = None):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        query = {"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}}
        if q:
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}}
            ]
        if category:
            query["categories"] = category
        if tag:
            query["tags"] = tag
            
        sort_mapping = {
            "latest": ("created_at", -1),
            "views": ("views", -1),
            "rating": ("average_rating", -1)
        }
        sort_field, sort_dir = sort_mapping.get(sort_by, ("created_at", -1))
        cursor = docs_collection.find(query).sort(sort_field, sort_dir).skip(offset).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def get_document_by_id(document_id: str, current_user, password: str = None):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        user_id = str(current_user.id) if current_user else None
        
        document = await docs_collection.find_one({"_id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tài liệu.")

        if document.get("is_password_protected") and document.get("author_id") != user_id:
            if not password:
                return {"id": str(document["_id"]), "title": document.get("title"), "is_password_protected": True}
            
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            if not pwd_context.verify(password, document.get("access_password_hash")):
                raise HTTPException(status_code=403, detail="Mật khẩu truy cập không chính xác.")
        
        document = serialize_document(document)
        if document["author_id"] != user_id and document["status"] != DocumentStatus.PUBLISHED:
            if not current_user or current_user.role != "ADMIN":
                raise HTTPException(status_code=403, detail="Tài liệu đang ở bản nháp.")
        
        return document

    @staticmethod
    async def soft_delete_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["documents"].update_one(
            {"_id": document_id, "author_id": str(current_user.id), "is_deleted": {"$ne": True}},
            {"$set": {"is_deleted": True, "deleted_at": datetime.datetime.now(timezone.utc)}}
        )
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        logger.info(f"Workspace: Document {document_id} moved to trash by {current_user.id}")
        return {"message": "Đã chuyển tài liệu vào thùng rác."}

    @staticmethod
    async def restore_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["documents"].update_one(
            {"_id": document_id, "author_id": str(current_user.id), "is_deleted": True},
            {"$set": {"is_deleted": False, "deleted_at": None}}
        )
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu trong thùng rác.")
            
        logger.info(f"Workspace: Document {document_id} restored by {current_user.id}")
        return {"message": "Đã khôi phục tài liệu thành công."}

    @staticmethod
    async def get_trash(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        docs = await db["documents"].find(
            {"author_id": str(current_user.id), "is_deleted": True}
        ).sort("deleted_at", -1).to_list(length=100)
        return [
            {
                "id": str(b["_id"]),
                "title": b.get("title", ""),
                "deleted_at": b["deleted_at"].isoformat() if isinstance(b.get("deleted_at"), datetime.datetime) else b.get("deleted_at"),
            }
            for b in docs
        ]

    @staticmethod
    async def set_document_password(document_id: str, password: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(password)
        await db["documents"].update_one(
            {"_id": document_id},
            {"$set": {"access_password_hash": hashed, "is_password_protected": True, "updated_at": datetime.datetime.now(timezone.utc)}}
        )
        logger.info(f"Workspace: Password protection enabled for {document_id}")
        return {"message": "Đã thiết lập mật khẩu bảo vệ tài liệu."}

    @staticmethod
    async def invite_coauthor(document_id: str, email: str, current_user):
        db = db_client.mongodb.get_default_database()
        document = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        target_user = await db["users"].find_one({"email": email})
        if not target_user:
            raise HTTPException(status_code=404, detail="Email không tồn tại.")
            
        if str(target_user["_id"]) in document.get("coauthors", []):
            return {"message": "Người này đã là đồng tác giả."}
            
        await db["documents"].update_one({"_id": document_id}, {"$addToSet": {"coauthors": str(target_user["_id"])}})
        logger.info(f"Workspace: Coauthor {target_user['_id']} invited to {document_id}")
        return {"message": f"Đã thêm {target_user['full_name']} làm đồng tác giả."}

    @staticmethod
    async def get_document_by_slug(slug: str, current_user=None):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        document = await docs_collection.find_one({"slug": slug, "status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}})
        if not document:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        
        user_id = str(current_user.id) if current_user else None
        has_purchased = False
        if user_id:
            if document.get("author_id") == user_id:
                has_purchased = True
            else:
                purchases_col = db["purchases"]
                purchase = await purchases_col.find_one({"user_id": user_id, "item_id": str(document["_id"])})
                if purchase:
                    has_purchased = True
        
        await docs_collection.update_one({"_id": document["_id"]}, {"$inc": {"views": 1}})
        document["views"] = document.get("views", 0) + 1
        document = serialize_document(document)
        
        author = await db["users"].find_one({"_id": document["author_id"]})
        if author:
            document["author"] = {
                "full_name": author.get("full_name") or author.get("username"),
                "avatar_url": author.get("avatar_url"),
                "slug": author.get("slug")
            }
        
        document["has_purchased"] = has_purchased
        return document

    @staticmethod
    async def export_epub(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        document = await db["documents"].find_one({"_id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        mem_zip = io.BytesIO()
        with zipfile.ZipFile(mem_zip, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("mimetype", "application/epub+zip")
            html_content = f'<?xml version="1.0" encoding="UTF-8"?><html xmlns="http://www.w3.org/1999/xhtml"><head><title>{document.get("title")}</title></head><body><h1>{document.get("title")}</h1>'
            content = document.get("content") or ""
            paragraphs = content.split("\n")
            html_body = "".join([f"<p>{p.strip()}</p>" for p in paragraphs if p.strip()])
            html_content += html_body + "</body></html>"
            zf.writestr("OEBPS/content.xhtml", html_content)
            
        mem_zip.seek(0)
        logger.info(f"Workspace: EPUB exported for {document_id}")
        return mem_zip.read()

    @staticmethod
    async def get_document_preview(slug: str) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"slug": slug, "status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
        
        preview_data = {
            "title": doc.get("title"),
            "description": doc.get("description"),
            "cover_url": doc.get("cover_url"),
            "author_id": doc.get("author_id"),
            "preview_content": doc.get("content", "")[:500] if doc.get("content") else ""
        }
        return preview_data

    @staticmethod
    async def get_document_audit_logs(document_id: str, current_user) -> list:
        db = db_client.mongodb.get_default_database()
        document = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)}, {"_id": 1})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")

        logs = await db["audit_logs"].find({"document_id": document_id}).sort("timestamp", -1).limit(100).to_list(length=100)
        return [
            {
                "id": str(log["_id"]),
                "action": log.get("action"),
                "actor_id": log.get("actor_id"),
                "reason": log.get("reason"),
                "timestamp": log["timestamp"].isoformat() if isinstance(log.get("timestamp"), datetime.datetime) else log.get("timestamp")
            }
            for log in logs
        ]

    @staticmethod
    async def get_approval_queue(skip: int = 0, limit: int = 30) -> list:
        db = db_client.mongodb.get_default_database()
        documents = await db["documents"].find({"status": "processing_publish"}).sort("updated_at", 1).skip(skip).limit(limit).to_list(length=limit)
        return [{
            "id": str(b["_id"]),
            "title": b.get("title", ""),
            "author_id": b.get("author_id"),
            "submitted_at": b.get("updated_at", dt.utcnow()).isoformat() if isinstance(b.get("updated_at"), dt) else ""
        } for b in documents]

    @staticmethod
    async def moderate_document(document_id: str, action: str, reason: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        status = "PUBLISHED" if action == "approve" else "REJECTED"
        await db["documents"].update_one(
            {"_id": document_id},
            {"$set": {"status": status, "moderation_reason": reason, "moderated_by": str(current_moderator.id), "moderated_at": dt.utcnow()}}
        )
        await db["audit_logs"].insert_one({
            "action": f"DOCUMENT_{status}", 
            "actor_id": str(current_moderator.id), 
            "document_id": document_id, 
            "reason": reason, 
            "timestamp": dt.utcnow()
        })
        logger.info(f"Moderation: Document {document_id} {status.lower()} by {current_moderator.id}")
        return {"message": f"Đã {status.lower()} tài liệu thành công."}

    @staticmethod
    async def resolve_copyright_dispute(dispute_id: str, resolution: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        await db["copyright_disputes"].update_one(
            {"_id": dispute_id}, 
            {"$set": {
                "status": "resolved", 
                "resolution": resolution, 
                "resolved_by": str(current_moderator.id), 
                "resolved_at": dt.utcnow()
            }}
        )
        logger.info(f"Moderation: Copyright dispute {dispute_id} resolved by {current_moderator.id}")
        return {"message": "Đã giải quyết tranh chấp bản quyền thành công."}
