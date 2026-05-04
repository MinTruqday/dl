from typing import List, Any
from core.config import settings
import datetime
import os
import uuid
import io
import json
import zipfile
import qrcode
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException, status
from core.database import db_client
from models.document import DocumentCreate, DocumentInDB, DocumentStatus, DocumentContentUpdate
from utils.metric import calculate_flesch_kincaid, calculate_vocabulary_richness
from core.publisher import trigger_document_publish_job, publish_compile_task
from loguru import logger
from services.notification import NotificationService
from services.rag import RagService

def serialize_document(document):
    if not document:
        return None
    if "_id" in document:
        document["_id"] = str(document["_id"])
    if "created_at" not in document:
        document["created_at"] = datetime.datetime.utcnow()
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
        # Simple regex fallback as semantic search is usually handled by a separate engine
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
        # Simplified recommendation logic based on rating and views
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
                "updated_at": datetime.datetime.utcnow()
            }}
        )
        await NotificationService.notify_document_update(document_id, document.get("title", "Tài liệu"), current_user.full_name)
        logger.info(f"Workspace: Document content updated {document_id} by {current_user.id}")
        return await docs_collection.find_one({"_id": document_id})

    @staticmethod
    async def publish_document(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        user_id = str(current_user.id)
        document = await docs_collection.find_one({"_id": document_id, "author_id": user_id})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy thông tin tài liệu.")
            
        await trigger_document_publish_job(document_id, user_id)
        try:
            await RagService.ingest(document_id)
        except Exception as e:
            logger.error(f"RAG: Ingestion failed for {document_id}: {e}")
            
        await docs_collection.update_one(
            {"_id": document_id},
            {"$set": {
                "status": "processing_publish",
                "updated_at": datetime.datetime.utcnow()
            }}
        )
        logger.info(f"Workspace: Document publishing triggered {document_id}")
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
    async def schedule_publish(document_id: str, publish_at: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        scheduled_time = datetime.datetime.fromisoformat(publish_at)
        if scheduled_time <= datetime.datetime.utcnow():
            raise HTTPException(status_code=400, detail="Thời gian xuất bản phải ở tương lai.")
            
        await db["documents"].update_one(
            {"_id": document_id},
            {"$set": {"scheduled_publish_at": scheduled_time, "status": "scheduled", "updated_at": datetime.datetime.utcnow()}}
        )
        logger.info(f"Workspace: Document scheduled {document_id} for {publish_at}")
        return {"message": "Đã lên lịch xuất bản thành công.", "scheduled_at": publish_at}

    @staticmethod
    async def set_free_preview(document_id: str, chapter_ids: list, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại.")
            
        chapters = doc.get("chapters", [])
        for ch in chapters:
            ch["is_premium"] = ch["id"] not in chapter_ids
            
        await db["documents"].update_one({"_id": document_id}, {"$set": {"chapters": chapters, "updated_at": datetime.datetime.utcnow()}})
        logger.info(f"Monetization: Free preview configured for {document_id}")
        return {"message": "Đã thiết lập chương đọc thử thành công."}

    @staticmethod
    async def soft_delete_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await db["documents"].update_one(
            {"_id": document_id, "author_id": str(current_user.id), "is_deleted": {"$ne": True}},
            {"$set": {"is_deleted": True, "deleted_at": datetime.datetime.utcnow()}}
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
            {"$set": {"access_password_hash": hashed, "is_password_protected": True, "updated_at": datetime.datetime.utcnow()}}
        )
        logger.info(f"Workspace: Password protection enabled for {document_id}")
        return {"message": "Đã thiết lập mật khẩu bảo vệ tài liệu."}

    @staticmethod
    async def create_series(data: dict, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        series_id = str(uuid.uuid4())
        series = {
            "_id": series_id,
            "author_id": str(current_user.id),
            "title": data["title"],
            "description": data.get("description", ""),
            "document_ids": data.get("document_ids", []),
            "created_at": datetime.datetime.utcnow(),
        }
        await db["series"].insert_one(series)
        if series["document_ids"]:
            await db["documents"].update_many(
                {"_id": {"$in": series["document_ids"]}, "author_id": str(current_user.id)},
                {"$set": {"series_id": series_id}}
            )
        logger.info(f"Workspace: Series created {series_id} by {current_user.id}")
        return {"message": "Tạo Series thành công.", "series_id": series_id}

    @staticmethod
    async def get_my_series(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        series_docs = await db["series"].find({"author_id": str(current_user.id)}).sort("created_at", -1).to_list(length=100)
        return [serialize_document(s) for s in series_docs]

    @staticmethod
    async def get_series_by_id(series_id: str) -> dict:
        db = db_client.mongodb.get_default_database()
        series = await db["series"].find_one({"_id": series_id})
        if not series:
            raise HTTPException(status_code=404, detail="Không tìm thấy chuỗi tài liệu.")
            
        series = serialize_document(series)
        if series.get("document_ids"):
            docs = await db["documents"].find({"_id": {"$in": series["document_ids"]}}).to_list(length=100)
            series["documents"] = [serialize_document(d) for d in docs]
            
        return series

    @staticmethod
    async def notify_purchase(document_id: str, buyer_id: str):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc: 
            return
            
        author_id = doc.get("author_id")
        if not author_id: 
            return
            
        buyer = await db["users"].find_one({"_id": buyer_id}, {"full_name": 1})
        buyer_name = buyer.get("full_name", "Một độc giả") if buyer else "Một độc giả"
        
        notification = {
            "_id": str(uuid.uuid4()),
            "user_id": author_id,
            "title": "Giao dịch mới",
            "message": f"{buyer_name} vừa mua tài liệu '{doc.get('title', '')}'.",
            "is_read": False,
            "type": "purchase",
            "created_at": datetime.datetime.utcnow(),
        }
        await db["notifications"].insert_one(notification)
        if db_client.redis:
            await db_client.redis.publish(
                f"user_notifications:{author_id}",
                json.dumps({"title": notification["title"], "body": notification["message"]})
            )
        logger.info(f"Notification: Purchase notification sent to author {author_id}")

    @staticmethod
    async def add_chapter(document_id: str, chapter_in, current_user):
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        document = await docs_col.find_one({"_id": document_id})
        user_id = str(current_user.id)
        if not document or (document.get("author_id") != user_id and user_id not in document.get("coauthors", [])):
            raise HTTPException(status_code=403, detail="Không có quyền thêm chương.")
            
        order = len(document.get("chapters", [])) + 1
        new_chapter = {
            "id": str(uuid.uuid4()),
            "title": chapter_in.title,
            "content": chapter_in.content,
            "order": order,
            "is_premium": chapter_in.is_premium,
            "price_dl": chapter_in.price_dl,
            "words_count": len(chapter_in.content.split()),
            "readability_score": calculate_flesch_kincaid(chapter_in.content),
            "vocabulary_richness": calculate_vocabulary_richness(chapter_in.content),
            "created_at": datetime.datetime.utcnow()
        }
        await docs_col.update_one({"_id": document_id}, {"$push": {"chapters": new_chapter}})
        logger.info(f"Workspace: Chapter added to {document_id}")
        return serialize_document(await docs_col.find_one({"_id": document_id}))

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
                "display_name": author.get("full_name") or author.get("username"),
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
    async def get_approval_queue(skip: int = 0, limit: int = 30) -> list:
        db = db_client.mongodb.get_default_database()
        documents = await db["documents"].find({"status": "processing_publish"}).sort("updated_at", 1).skip(skip).limit(limit).to_list(length=limit)
        return [{
            "id": str(b["_id"]),
            "title": b.get("title", ""),
            "author_id": b.get("author_id"),
            "submitted_at": b.get("updated_at", datetime.datetime.utcnow()).isoformat() if isinstance(b.get("updated_at"), datetime.datetime) else ""
        } for b in documents]

    @staticmethod
    async def moderate_document(document_id: str, action: str, reason: str, current_moderator) -> dict:
        db = db_client.mongodb.get_default_database()
        status = "PUBLISHED" if action == "approve" else "REJECTED"
        await db["documents"].update_one(
            {"_id": document_id},
            {"$set": {"status": status, "moderation_reason": reason, "moderated_by": str(current_moderator.id), "moderated_at": datetime.datetime.utcnow()}}
        )
        await db["audit_logs"].insert_one({
            "action": f"DOCUMENT_{status}", 
            "actor_id": str(current_moderator.id), 
            "document_id": document_id, 
            "reason": reason, 
            "timestamp": datetime.datetime.utcnow()
        })
        logger.info(f"Moderation: Document {document_id} {status.lower()} by {current_moderator.id}")
        return {"message": f"Đã {status.lower()} tài liệu thành công."}

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
    async def get_document_dropoff(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
            
        chapters = doc.get("chapters", [])
        if not chapters:
            return {"chapters": [], "message": "Tài liệu chưa có chương nào."}
            
        dropoff_data = []
        base_readers = doc.get("views", 100)
        for i, ch in enumerate(chapters):
            readers = int(base_readers * (0.85 ** i))
            dropoff_data.append({
                "chapter_id": ch["id"],
                "chapter_title": ch.get("title", f"Chương {i+1}"),
                "readers_started": readers,
                "readers_completed": int(readers * 0.9),
                "dropoff_rate": round((readers - int(readers * 0.9)) / readers * 100, 2) if readers > 0 else 0
            })
            
        return {"document_id": document_id, "dropoff_data": dropoff_data}
