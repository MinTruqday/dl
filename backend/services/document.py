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
from core.document_metrics import calculate_flesch_kincaid, calculate_vocabulary_richness
from core.publisher import trigger_document_publish_job, publish_compile_task
from loguru import logger

def serialize_document(document):
    if not document:
        return None
    if "_id" in document:
        document["_id"] = str(document["_id"])
    if "created_at" not in document:
        document["created_at"] = datetime.datetime.utcnow()
    if "author_id" not in document:
        document["author_id"] = "Unknown"
    return document

from services.notification import NotificationService

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
    async def create_document(doc_in: DocumentCreate, current_user):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        existing_slug = await docs_collection.find_one({"slug": doc_in.slug})
        if existing_slug:
            raise HTTPException(status_code=400, detail="Đường dẫn tài liệu này đã tồn tại, hãy chọn tên khác.")
        doc_dict = doc_in.model_dump()
        doc_doc = DocumentInDB(**doc_dict, author_id=str(current_user.id))
        await docs_collection.insert_one(doc_doc.model_dump(by_alias=True))
        return doc_doc

    @staticmethod
    async def update_document_content(document_id: str, content_in: DocumentContentUpdate, current_user):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        document = await docs_collection.find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu hoặc bạn không có quyền.")
        await docs_collection.update_one(
            {"_id": document_id},
            {"$set": {
                "content": content_in.content, 
                "content_format": content_in.content_format,
                "updated_at": datetime.datetime.utcnow()
            }}
        )
        await NotificationService.notify_document_update(document_id, document.get("title", "Tài liệu"), current_user.full_name)
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
        await docs_collection.update_one(
            {"_id": document_id},
            {"$set": {
                "status": "processing_publish",
                "updated_at": datetime.datetime.utcnow()
            }}
        )
        return await docs_collection.find_one({"_id": document_id})

    @staticmethod
    async def list_documents(limit: int, offset: int, q: str, sort_by: str, category: str = None, tag: str = None):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        query = {"status": DocumentStatus.PUBLISHED}
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
    async def get_trending_documents(limit: int = 5):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        cursor = docs_collection.find({"status": DocumentStatus.PUBLISHED}).sort("views", -1).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def get_document_by_id(document_id: str, current_user, password: str = None):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        user_id = str(current_user.id) if current_user else None
        
        try:
            query_id = str(document_id)
        except InvalidId:
            raise HTTPException(status_code=400, detail="ID tài liệu không hợp lệ.")
            
        document = await docs_collection.find_one({"_id": query_id})
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
            if not current_user or getattr(current_user, "role", "") != "ADMIN":
                raise HTTPException(status_code=403, detail="Tài liệu đang ở bản nháp, bạn không có quyền xem.")
        
        if document.get("chapters") and document["author_id"] != user_id and (not current_user or getattr(current_user, "role", "") != "ADMIN"):
            try:
                purchases_col = db_client.mongodb.get_database("doclib").get_collection("purchases")
                user_purchases = await purchases_col.find({"user_id": user_id, "item_type": "chapter"}).to_list(length=1000)
                owned_chapter_ids = {p["item_id"] for p in user_purchases}
                for chapter in document.get("chapters", []):
                    if chapter.get("is_premium") and chapter.get("id") not in owned_chapter_ids:
                        chapter["content"] = ""
                        chapter["locked"] = True
                    else:
                        chapter["locked"] = False
            except Exception as e:
                logger.error(f"Error parsing chapters: {e}")
        return document

    @staticmethod
    async def verify_document_password(document_id: str, password: str) -> bool:
        db = db_client.mongodb.get_default_database()
        document = await db["documents"].find_one({"_id": document_id})
        if not document or not document.get("is_password_protected"):
            return True
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        return pwd_context.verify(password, document.get("access_password_hash"))


    @staticmethod
    async def request_compilation(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        user_id = str(current_user.id)
        document = await docs_collection.find_one({"_id": document_id, "author_id": user_id})
        if not document:
            raise HTTPException(status_code=404, detail="Bạn không có quyền chuyển đổi định dạng tài liệu này.")
        await docs_collection.update_one(
            {"_id": document_id},
            {"$set": {"status": "compiling", "updated_at": datetime.datetime.utcnow()}}
        )
        actual_content = document.get("content") or ""
        content_format = document.get("content_format", "latex")
        if content_format != "latex" or not actual_content.strip():
            actual_content = ""
        success = await publish_compile_task(document_id, user_id, actual_content)
        if not success:
             raise HTTPException(status_code=500, detail="Máy chủ đang bận, không thể xuất bản tài liệu lúc này. Vui lòng thử lại sau.")
        return {"message": "Đang xuất file PDF, vui lòng chờ.", "status": "compiling"}

    @staticmethod
    async def get_document_by_slug(slug: str):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        document = await docs_collection.find_one({"slug": slug, "status": DocumentStatus.PUBLISHED})
        if not document:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại hoặc chưa xuất bản.")
        await docs_collection.update_one({"_id": document["_id"]}, {"$inc": {"views": 1}})
        document["views"] = document.get("views", 0) + 1
        return document

    @staticmethod
    async def update_cover(document_id: str, cover_url: str, current_user):
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        document = await docs_col.find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not document:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại hoặc bạn không có quyền.")
        await docs_col.update_one(
            {"_id": document_id},
            {"$set": {"cover_url": cover_url, "updated_at": datetime.datetime.utcnow()}}
        )
        return serialize_document(await docs_col.find_one({"_id": document_id}))

    @staticmethod
    async def add_chapter(document_id: str, chapter_in, current_user):
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        document = await docs_col.find_one({"_id": document_id})
        user_id = str(current_user.id)
        if not document or (document.get("author_id") != user_id and user_id not in document.get("coauthors", [])):
            raise HTTPException(status_code=403, detail="Bạn không có quyền thêm chương mới cho tài liệu này.")
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
        return serialize_document(await docs_col.find_one({"_id": document_id}))

    @staticmethod
    async def invite_coauthor(document_id: str, email: str, current_user):
        db = db_client.mongodb.get_default_database()
        document = await db["documents"].find_one({"_id": document_id, "author_id": str(current_user.id)})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu hoặc không phải chủ sở hữu.")
        target_user = await db["users"].find_one({"email": email})
        if not target_user:
            raise HTTPException(status_code=404, detail="Email này không tồn tại.")
        if target_user["_id"] in document.get("coauthors", []):
            return {"message": "Người này đã là đồng tác giả."}
        await db["documents"].update_one({"_id": document_id}, {"$addToSet": {"coauthors": target_user["_id"]}})
        return {"message": f"Đã thêm {target_user['full_name']} làm đồng tác giả."}

    @staticmethod
    async def compile_document_latex(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        docs_collection = db["documents"]
        user_id = str(current_user.id)
        document = await docs_collection.find_one({"_id": document_id, "author_id": user_id})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu.")
        content_raw = document.get("content", "")
        if not db_client.rabbitmq:
            raise HTTPException(status_code=500, detail="Máy chủ đang bận, không thể xuất bản lúc này.")
        from aio_pika import Message, DeliveryMode
        channel = await db_client.rabbitmq.channel()
        payload = json.dumps({
            "document_id": document_id,
            "author_id": user_id,
            "content_raw": content_raw
        }).encode("utf-8")
        await channel.default_exchange.publish(
            Message(body=payload, content_type="application/json", delivery_mode=DeliveryMode.PERSISTENT),
            routing_key="tectonic_queue"
        )
        await docs_collection.update_one({"_id": document_id}, {"$set": {"status": "compiling_latex"}})
        return {"status": "success", "message": "Đang xử lý công thức toán học."}

    @staticmethod
    async def export_epub(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        document = await db["documents"].find_one({"_id": str(document_id)})
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
        return mem_zip.read()

    @staticmethod
    async def generate_qr_code(document_id: str):
        app_url = getattr(settings, "URL", None)
        img = qrcode.make(f"{app_url}/reader/{document_id}")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    @staticmethod
    async def link_series(document_id: str, series_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        await db["documents"].update_one({"_id": document_id}, {"$set": {"series_id": series_id}})
        return {"message": "Đã liên kết Series thành công"}

    @staticmethod
    async def set_warnings(document_id: str, warnings: list[str], current_user):
        db = db_client.mongodb.get_default_database()
        await db["documents"].update_one({"_id": document_id}, {"$set": {"content_warnings": warnings}})
        return {"message": "Đã thiết lập cảnh báo nội dung."}

    @staticmethod
    async def set_custom_design(document_id: str, custom_css: str, custom_font: str, current_user):
        db = db_client.mongodb.get_default_database()
        await db["documents"].update_one({"_id": document_id}, {"$set": {"custom_css": custom_css, "custom_font": custom_font}})
        return {"message": "Đã lưu thiết kế tuỳ chỉnh."}

    @staticmethod
    async def get_ai_recommendations(limit: int, reference_document_id: str = None):
        db = db_client.mongodb.get_default_database()
        
        import os
        import httpx
        rag_url = getattr(settings, "AGENTIC_RAG_URL", None)
        
        if reference_document_id and rag_url:
            try:
                ref_doc = await db["documents"].find_one({"_id": reference_document_id})
                if ref_doc:
                    async with httpx.AsyncClient() as client:
                        prompt = f"Given a document titled '{ref_doc.get('title')}' with description '{ref_doc.get('description', '')}', recommend 5 similar themes or topics as JSON array of strings."
                        res = await client.post(
                            f"{rag_url}/api/inference/generate_raw",
                            json={"prompt": prompt, "max_tokens": 100, "temperature": 0.5},
                            timeout=5.0
                        )
                        if res.status_code == 200:
                            query = {"status": DocumentStatus.PUBLISHED, "_id": {"$ne": reference_document_id}}
                            cursor = db["documents"].find(query).limit(limit)
                            documents = await cursor.to_list(length=limit)
                            return [{"document_id": str(d["_id"]), "score": 0.95, "title": d.get("title", "Untitled"), "cover_url": d.get("cover_url")} for d in documents]
            except Exception as e:
                logger.error(f"AI Recommendation error via RAG: {e}")

        query = {"status": DocumentStatus.PUBLISHED}
        if reference_document_id:
            query["_id"] = {"$ne": reference_document_id}
            
        cursor = db["documents"].find(query).limit(limit)
        documents = await cursor.to_list(length=limit)
        
        if len(documents) < limit:
            extra = await db["documents"].aggregate([
                {"$match": {"status": DocumentStatus.PUBLISHED, "_id": {"$ne": reference_document_id}}},
                {"$sample": {"size": limit - len(documents)}}
            ]).to_list(length=limit - len(documents))
            documents.extend(extra)
            
        return [{"document_id": str(d["_id"]), "score": 0.8, "title": d.get("title", "Untitled"), "cover_url": d.get("cover_url")} for d in documents]

    @staticmethod
    async def get_seo_meta(document_id: str):
        db = db_client.mongodb.get_default_database()
        try:
            query_id = str(document_id)
        except InvalidId:
            query_id = document_id
        document = await db["documents"].find_one({"_id": query_id})
        if not document:
            return {
                 "title": "Tài liệu không tồn tại | DocLib",
                 "description": "Không tìm thấy nội dung.",
                 "keywords": ["doclib", "tài liệu"]
            }
        return {
            "title": f"{document.get('title', 'Untitled')} | DocLib",
            "description": document.get('description', 'Một tác phẩm học thuật trên DocLib.')[:150],
            "keywords": document.get("tags", []) + ["doclib", "tài liệu", "reading"]
        }

    @staticmethod
    async def get_document_preview(document_id: str) -> dict:
        db = db_client.mongodb.get_default_database()
        document = await db["documents"].find_one({"_id": document_id, "status": DocumentStatus.PUBLISHED})
        if not document:
            raise HTTPException(status_code=404, detail="Tài liệu không tồn tại hoặc chưa xuất bản.")
        chapters = document.get("chapters", [])
        preview_chapters = []
        for ch in chapters[:2]:
            preview_chapters.append({
                "title": ch.get("title", ""),
                "content": ch.get("content", "")[:1500],
                "is_preview": True,
            })
        return {
            "id": str(document["_id"]),
            "title": document.get("title", ""),
            "slug": document.get("slug", ""),
            "description": document.get("description", ""),
            "author_id": document.get("author_id", ""),
            "cover_url": document.get("cover_url"),
            "tags": document.get("tags", []),
            "average_rating": document.get("average_rating"),
            "rating_count": document.get("rating_count", 0),
            "views": document.get("views", 0),
            "total_chapters": len(chapters),
            "preview_chapters": preview_chapters,
        }

    @staticmethod
    async def get_semantic_search(query: str, limit: int):
        db = db_client.mongodb.get_default_database()
        docs_col = db["documents"]
        cursor = docs_col.find({"$text": {"$search": query}}).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]
