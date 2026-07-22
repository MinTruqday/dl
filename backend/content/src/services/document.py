from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.redis import redis
from src.core.infrastructure.mongo import mongo
import io
import json
import os
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Any, List

import httpx
from bson import ObjectId
from fastapi import HTTPException, Query, status
from loguru import logger
from passlib.context import CryptContext
from src.core.publication import trigger_document_publish_job
from src.schemas.document import (
    DocumentContentUpdate,
    DocumentCreate,
    DocumentInDB,
    DocumentStatus,
)
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.document import DocumentRepository

def serialize_document(document):
    if not document:
        return None
    if "_id" in document:
        document["_id"] = str(document["_id"])
    if "created_at" not in document:
        document["created_at"] = datetime.now(timezone.utc)
    views = document.get("views", 0)
    document["view_count"] = views
    document["views_count"] = views
    document.pop("password", None)
    document.pop("access_password_hash", None)
    return document

class DocumentService:
    @staticmethod
    def _is_admin(current_user) -> bool:
        role = getattr(current_user, "role", "") if current_user else ""
        return str(getattr(role, "value", role)).lower() == "admin"

    @staticmethod
    async def _has_purchase(user_id: str | None, document_id: str) -> bool:
        if not user_id:
            return False
        purchase = await database.mongodb[settings.FINANCE_DB_NAME].purchases.find_one(
            {"user_id": user_id, "item_id": document_id, "status": "purchased"},
            {"_id": 1},
        )
        return purchase is not None

    @staticmethod
    async def _can_read_full(document: dict, current_user) -> bool:
        user_id = str(current_user.id) if current_user else None
        if user_id == document.get("creator_id") or DocumentService._is_admin(current_user):
            return True
        if document.get("status") != DocumentStatus.PUBLISHED or document.get("is_deleted") is True:
            return False
        if document.get("visibility", "public") != "public":
            return False
        if int(document.get("price_dl", 0) or 0) <= 0 and not document.get("is_premium"):
            return True
        return await DocumentService._has_purchase(user_id, str(document["_id"]))

    @staticmethod
    def _fragment_document_content(content: str, key: bytes = None) -> list:
        if not content:
            return []
        import base64
        import os
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            AESGCM = None

        if key and AESGCM:
            aesgcm = AESGCM(key)
            chunk_size = 50000
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            fragments = []
            for chunk in chunks:
                nonce = os.urandom(12)
                ct = aesgcm.encrypt(nonce, chunk.encode('utf-8'), None)
                encoded = base64.b64encode(nonce + ct).decode('utf-8')
                fragments.append(encoded)
            return fragments
        else:
            chunk_size = 50
            chunks = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
            fragments = []
            for chunk in chunks:
                encoded = base64.b64encode(chunk.encode('utf-8')).decode('utf-8')
                fragments.append(encoded)
            return fragments

    @staticmethod
    @log_logic_execution
    async def get_tags_categories():
        
        docs_col = DocumentRepository
        pipeline_tags = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags"}},
            {"$sort": {"_id": 1}},
        ]
        pipeline_categories = [
            {"$match": {"category": {"$type": "string"}}},
            {"$group": {"_id": "$category"}},
            {"$sort": {"_id": 1}},
        ]
        tags_list = await docs_col.aggregate(pipeline_tags).to_list(length=None)
        categories_list = await docs_col.aggregate(pipeline_categories).to_list(length=None)
        return {
            "tags": [tag["_id"] for tag in tags_list],
            "categories": [category["_id"] for category in categories_list],
        }

    @staticmethod
    @log_logic_execution
    async def get_trending_documents(
        limit: int = Query(
            default=20, le=100
        )
    ) -> List[dict]:
        
        docs_col = DocumentRepository
        cursor = (
            docs_col.find(
                {"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}, "visibility": "public"}
            )
            .sort("views", -1)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    @log_logic_execution
    async def get_text_search(
        query: str,
        limit: int = Query(
            default=20, le=100
        ),
    ) -> List[dict]:
        
        docs_col = DocumentRepository
        cursor = docs_col.find(
            {
                "status": DocumentStatus.PUBLISHED,
                "is_deleted": {"$ne": True},
                "visibility": "public",
                "$text": {"$search": query},
            }
        ).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]


    @staticmethod
    @log_logic_execution
    async def import_document_from_file(file, current_user) -> dict:
        import hashlib
        import uuid
        import base64
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from src.core.infrastructure.mongo import mongo
        
        content_bytes = await file.read()
        if len(content_bytes) < 60:
            raise ValueError("Tệp tin không hợp lệ hoặc bị hỏng")
            
        file_id_bytes = content_bytes[:16]
        file_hash = content_bytes[16:48]
        nonce = content_bytes[48:60]
        ciphertext = content_bytes[60:]
        
        file_id = str(uuid.UUID(bytes=file_id_bytes))
        
        license_doc = await database.mongodb[settings.DRM_DB_NAME].drm_licenses.find_one({"file_id": file_id})
        if not license_doc:
            raise ValueError("Không tìm thấy giấy phép hợp lệ cho tài liệu này")
        if license_doc.get("status") != "ACTIVE":
            raise ValueError("Giấy phép tài liệu đã hết hiệu lực")
        if license_doc.get("user_id") != str(current_user.id) and not DocumentService._is_admin(current_user):
            raise ValueError("Bạn không có quyền truy cập tài liệu này")
            
        encoded_key = license_doc.get("aes_key")
        if not encoded_key:
            raise ValueError("Giấy phép tài liệu bị hỏng (thiếu khóa giải mã)")
            
        aes_key = base64.b64decode(encoded_key)
        
        try:
            aesgcm = AESGCM(aes_key)
            decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
        except Exception:
            raise ValueError("Giải mã tài liệu thất bại, tệp tin có thể đã bị can thiệp")
            
        if hashlib.sha256(decrypted_data).digest() != file_hash:
            raise ValueError("Dữ liệu tài liệu không toàn vẹn")
            
        raw_content = decrypted_data.decode("utf-8")
        ext = file.filename.split(".")[-1].lower() if file.filename else "doclib"
        content_format = "doclibx" if ext == "doclibx" else "doclib"
        
        from src.schemas.document import DocumentCreate
        
        doc_in = DocumentCreate(
            title=file.filename.split(".")[0] if file.filename else "Imported Document",
            content=raw_content,
            content_format=content_format
        )
        return await DocumentService.create_document(doc_in, current_user)


    @staticmethod
    @log_logic_execution
    async def create_document(doc_in: DocumentCreate, current_user):
        docs_collection = DocumentRepository
        import re
        import unicodedata

        slug = doc_in.slug
        if not slug:
            normalized = unicodedata.normalize("NFKD", doc_in.title).encode("ascii", "ignore").decode("ascii").lower()
            slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "tai-lieu"
        existing_slug = await docs_collection.find_one({"slug": slug})
        if existing_slug:
            slug = f"{slug}-{str(uuid7())[:8]}"

        doc_dict = doc_in.model_dump(exclude={"password"})
        doc_dict["slug"] = slug
        if not doc_dict.get("publisher_name"):
            doc_dict["publisher_name"] = current_user.full_name

        doc_doc = DocumentInDB(**doc_dict, creator_id=str(current_user.id))
        stored_document = doc_doc.model_dump(by_alias=True)
        if doc_in.password:
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            stored_document["access_password_hash"] = pwd_context.hash(doc_in.password)
            stored_document["is_password_protected"] = True
        await docs_collection.insert_one(stored_document)
        logger.info("Document successfully created in the system")
        return doc_doc

    @staticmethod
    @log_logic_execution
    async def get_my_documents(
        current_user,
        q: str = None,
        cursor: str = None,
        limit: int = Query(
            default=20, le=100
        ),
    ) -> list:
        
        query = {"creator_id": str(current_user.id), "is_deleted": {"$ne": True}}
        if q:
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
            ]
        if cursor:
            query["_id"] = {"$lt": cursor}

        docs = await (
            DocumentRepository
            .find(query)
            .sort("_id", -1)
            .to_list(length=limit)
        )
        return [
            {
                "_id": str(b["_id"]),
                "title": b.get("title", ""),
                "slug": b.get("slug", ""),
                "status": b.get("status", "draft"),
                "content_format": b.get("content_format", "doclib"),
                "cover_url": b.get("cover_url"),
                "views": b.get("views", 0),
                "created_at": (
                    b["created_at"].isoformat()
                    if isinstance(b.get("created_at"), datetime)
                    else b.get("created_at")
                ),
            }
            for b in docs
        ]

    @staticmethod
    @log_logic_execution
    async def update_document_content(
        document_id: str, content_in: DocumentContentUpdate, current_user
    ):
        
        docs_collection = DocumentRepository
        document = await docs_collection.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not document:
            raise HTTPException(status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu")

        if content_in.expected_version:
            db_updated = document.get("updated_at")
            if (
                db_updated
                and str(db_updated).split("+")[0]
                != str(content_in.expected_version).split("+")[0]
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Xung đột phiên bản: Tài liệu đã được cập nhật bởi một phiên làm việc khác",
                )

        if document.get("content"):
            await DocumentRepository.insert_revision(
                {
                    "document_id": document_id,
                    "creator_id": str(current_user.id),
                    "content": document.get("content"),
                    "content_format": document.get("content_format"),
                    "created_at": datetime.now(timezone.utc),
                    "note": "Auto-saved revision before update",
                }
            )

        await docs_collection.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "content": content_in.content,
                    "content_format": content_in.content_format,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if settings.NOTIFICATION_URL:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{settings.NOTIFICATION_URL}/thong-bao/gui-di",
                        json={
                            "target_user_id": str(current_user.id),
                            "title": "Document successfully updated",
                            "body": "The specified document content has been successfully synchronized and updated",
                            "type": "DOCUMENT_UPDATE",
                        },
                        headers={"X-Internal-Token": settings.SECRET_KEY},
                    )
                    response.raise_for_status()
            except Exception:
                logger.exception("Document update notification dispatch failed")

        logger.info("Document content successfully synchronized and updated")

        if redis:
            await redis.delete(f"document:{document_id}")
            if document.get("slug"):
                await redis.delete(f"document:slug:{document.get('slug')}")

        return serialize_document(await docs_collection.find_one({"_id": document_id}))

    @staticmethod
    @log_logic_execution
    async def update_document(document_id: str, doc_update, current_user) -> dict:
        
        docs_col = DocumentRepository
        doc = await docs_col.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")
        if (
            doc.get("creator_id") != str(current_user.id)
            and not DocumentService._is_admin(current_user)
        ):
            raise HTTPException(
                status_code=403, detail="Bạn không có quyền chỉnh sửa tài liệu này"
            )

        if hasattr(doc_update, "expected_version") and doc_update.expected_version:
            db_updated = doc.get("updated_at")
            if (
                db_updated
                and str(db_updated).split("+")[0]
                != str(doc_update.expected_version).split("+")[0]
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Không thể chỉnh sửa do đã có phiên bản mới hơn",
                )

        update_data = {
            k: v for k, v in doc_update.model_dump().items() if v is not None
        }
        if "slug" in update_data and update_data["slug"] != doc.get("slug"):
            existing = await docs_col.find_one({"slug": update_data["slug"]})
            if existing:
                raise HTTPException(
                    status_code=400, detail="Đường dẫn định tuyến đã được sử dụng"
                )

        if update_data:
            if doc.get("content") and "content" in update_data:
                await DocumentRepository.insert_revision(
                    {
                        "document_id": document_id,
                        "creator_id": str(current_user.id),
                        "content": doc.get("content"),
                        "content_format": doc.get("content_format"),
                        "created_at": datetime.now(timezone.utc),
                        "note": "Auto-saved revision before update",
                    }
                )

            update_data["updated_at"] = datetime.now(timezone.utc)
            await docs_col.update_one({"_id": document_id}, {"$set": update_data})

        if redis:
            await redis.delete(f"document:{document_id}")
            if doc.get("slug"):
                await redis.delete(f"document:slug:{doc.get('slug')}")

        return serialize_document(await docs_col.find_one({"_id": document_id}))

    @staticmethod
    @log_logic_execution
    async def list_documents(
        limit: int,
        cursor: str,
        q: str,
        sort_by: str,
        category: str = None,
        tag: str = None,
    ):
        
        docs_collection = DocumentRepository
        query = {"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}, "visibility": "public"}
        if q:
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
            ]
        if category:
            query["category"] = category
        if tag:
            query["tags"] = tag

        sort_mapping = {
            "latest": ("created_at", -1),
            "views": ("views", -1),
        }
        sort_field, sort_dir = sort_mapping.get(sort_by, ("created_at", -1))

        if cursor:
            if sort_field == "created_at":
                query["_id"] = {"$lt": cursor}

        cursor_db = docs_collection.find(query).sort(sort_field, sort_dir).limit(limit)
        documents = await cursor_db.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    @log_logic_execution
    async def get_document_by_id(document_id: str, current_user, password: str = None):
        
        docs_collection = DocumentRepository
        user_id = str(current_user.id) if current_user else None

        document = await docs_collection.find_one({"_id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")

        if document.get("is_deleted") is True and document.get("creator_id") != user_id and not DocumentService._is_admin(current_user):
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")

        if (
            document.get("creator_id") != user_id
            and document.get("status") != DocumentStatus.PUBLISHED
        ):
            if not DocumentService._is_admin(current_user):
                raise HTTPException(
                    status_code=403, detail="Tài liệu hiện đang ở trạng thái nháp và chưa được công bố"
                )

        if (
            document.get("is_password_protected")
            and document.get("creator_id") != user_id
        ):
            if not password:
                return {
                    "_id": str(document["_id"]),
                    "title": document.get("title"),
                    "is_password_protected": True,
                }

            rl_key = None
            if redis:
                rl_key = f"rl:unlock:{document_id}:{user_id or 'guest'}"
                attempts = await redis.get(rl_key)
                if attempts and int(attempts) >= 5:
                    raise HTTPException(
                        status_code=429,
                        detail="Truy cập bị tạm khóa do vi phạm giới hạn thử mật khẩu tài liệu",
                    )

            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            if not pwd_context.verify(password, document.get("access_password_hash")):
                if rl_key and redis:
                    await redis.incr(rl_key)
                    await redis.expire(rl_key, 900)
                raise HTTPException(
                    status_code=403,
                    detail="Thông tin xác thực không chính xác hoặc không khớp với hồ sơ bảo mật",
                )

            if rl_key and redis:
                await redis.delete(rl_key)

        can_read_full = await DocumentService._can_read_full(document, current_user)
        if not can_read_full and document.get("status") == DocumentStatus.PUBLISHED:
            raw_content = document.get("content") or ""
            limit = max(0, int(document.get("preview_pages", 5) or 0))
            document["content"] = raw_content[: limit * 1000]
            document["has_purchased"] = False

        document = serialize_document(document)

        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import base64
        aes_key = AESGCM.generate_key(bit_length=256)
        b64_key = base64.b64encode(aes_key).decode("utf-8")
        if redis and can_read_full:
            uid_str = user_id or "guest"
            await redis.setex(f"aes_key:{document['_id']}:{uid_str}", 300, b64_key)

        try:
            from src.core.infrastructure.mongo import mongo
            drm_doc = await database.mongodb[settings.DRM_DB_NAME].document_drm_settings.find_one({"document_id": document["_id"]})
            if drm_doc:
                document["drm_settings"] = {
                    "disable_copy": drm_doc.get("disable_copy", False),
                    "hide_from_search": drm_doc.get("hide_from_search", False),
                }
        except Exception:
            logger.exception("Failed to retrieve DRM settings")

        if document.get("content"):
            if user_id != document.get("creator_id") and can_read_full:
                document["content_fragments"] = DocumentService._fragment_document_content(document.get("content"), aes_key)
                del document["content"]

        return document

    @staticmethod
    @log_logic_execution
    async def soft_delete_document(document_id: str, current_user) -> dict:
        
        res = await DocumentRepository.update_one(
            {
                "_id": document_id,
                "creator_id": str(current_user.id),
                "is_deleted": {"$ne": True},
            },
            {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc)}},
        )
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")

        logger.info("Document successfully moved to the recycle bin")
        return {"message": "Tài liệu đã được di chuyển vào thùng rác hệ thống"}

    @staticmethod
    @log_logic_execution
    async def restore_document(document_id: str, current_user) -> dict:
        
        res = await DocumentRepository.update_one(
            {
                "_id": document_id,
                "creator_id": str(current_user.id),
                "is_deleted": True,
            },
            {"$set": {"is_deleted": False, "deleted_at": None}},
        )
        if res.modified_count == 0:
            raise HTTPException(
                status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu trong thùng rác"
            )

        logger.info("Document successfully restored from the recycle bin")
        return {"message": "Tài liệu đã được khôi phục hoàn tất từ thùng rác"}

    @staticmethod
    @log_logic_execution
    async def get_trash(current_user) -> list:
        
        docs = await (
            DocumentRepository
            .find({"creator_id": str(current_user.id), "is_deleted": True})
            .sort("deleted_at", -1)
            .to_list(length=100)
        )
        return [
            {
                "_id": str(b["_id"]),
                "title": b.get("title", ""),
                "deleted_at": (
                    b["deleted_at"].isoformat()
                    if isinstance(b.get("deleted_at"), datetime)
                    else b.get("deleted_at")
                ),
            }
            for b in docs
        ]

    @staticmethod
    @log_logic_execution
    async def set_document_password(
        document_id: str, password: str, current_user
    ) -> dict:
        
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(password)
        await DocumentRepository.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "access_password_hash": hashed,
                    "is_password_protected": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Document password protection enabled successfully")
        return {"message": "Thiết lập mật khẩu bảo vệ tài liệu hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def invite_coauthor(document_id: str, email: str, current_user):
        
        document = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not document:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")

        target_user = None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.HUMANITY_URL}/nguoi-dung/email/{email}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                if resp.status_code == 200:
                    target_user = resp.json().get("data")
        except Exception:
            logger.exception("Author profile synchronization failed")

        if not target_user:
            raise HTTPException(
                status_code=404, detail="Hệ thống không tìm thấy tài khoản liên kết với địa chỉ email cung cấp"
            )

        if str(target_user["_id"]) in document.get("coauthors", []):
            return {"message": "Tài khoản yêu cầu đã là thành viên cộng tác của tài liệu này"}

        await DocumentRepository.update_one(
            {"_id": document_id}, {"$addToSet": {"coauthors": str(target_user["_id"])}}
        )
        logger.info("Collaboration invitation sent successfully")
        return {"message": "Gửi lời mời tham gia cộng tác hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_document_by_slug(slug: str, current_user=None):
        
        docs_collection = DocumentRepository
        document = await docs_collection.find_one(
            {
                "slug": slug,
                "status": DocumentStatus.PUBLISHED,
                "is_deleted": {"$ne": True},
                "visibility": "public",
            }
        )
        if not document:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")

        user_id = str(current_user.id) if current_user else None
        has_purchased = False
        if user_id:
            if document.get("creator_id") == user_id:
                has_purchased = True
            else:
                has_purchased = await DocumentService._has_purchase(user_id, str(document["_id"]))

        is_privileged = DocumentService._is_admin(current_user)
        requires_purchase = int(document.get("price_dl", 0) or 0) > 0 or document.get("is_premium")
        if requires_purchase and not has_purchased and not is_privileged:
            raw_content = document.get("content") or ""
            limit = document.get("preview_pages", 5)
            try:
                import json

                parsed = json.loads(raw_content)
                if "blocks" in parsed:
                    parsed["blocks"] = parsed["blocks"][: limit * 5]
                    document["content"] = json.dumps(parsed)
                else:
                    document["content"] = raw_content[: limit * 1000]
            except (TypeError, ValueError, json.JSONDecodeError):
                document["content"] = raw_content[: limit * 1000]

        should_increment = True
        if user_id == document.get("creator_id"):
            should_increment = False
        elif redis:
            cache_key = f"viewed:{user_id or 'guest'}:{document['_id']}"
            if await redis.get(cache_key):
                should_increment = False
            else:
                await redis.setex(cache_key, 600, "1")

        if should_increment:
            await docs_collection.update_one(
                {"_id": document["_id"]}, {"$inc": {"views": 1}}
            )
            document["views"] = document.get("views", 0) + 1
        document = serialize_document(document)

        author = None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.HUMANITY_URL}/nguoi-dung/{document['creator_id']}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                if resp.status_code == 200:
                    author = resp.json().get("data")
        except Exception:
            logger.exception("Failed to synchronize author profile data")
        if author:
            document["author"] = {
                "full_name": author.get("full_name") or author.get("username"),
                "avatar_url": author.get("avatar_url"),
                "slug": author.get("slug"),
            }

        document["has_purchased"] = has_purchased
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        import base64
        aes_key = AESGCM.generate_key(bit_length=256)
        b64_key = base64.b64encode(aes_key).decode("utf-8")
        if redis and (has_purchased or not requires_purchase or is_privileged):
            uid_str = user_id or "guest"
            await redis.setex(f"aes_key:{document['_id']}:{uid_str}", 300, b64_key)
        
        if document.get("content"):
            if user_id != document.get("creator_id") and (has_purchased or not requires_purchase or is_privileged):
                document["content_fragments"] = DocumentService._fragment_document_content(document.get("content"), aes_key)
                del document["content"]
            
        return document

    @staticmethod
    @log_logic_execution
    async def get_document_decryption_key(document_id: str, current_user):
        user_id = str(current_user.id) if current_user else "guest"
        document = await DocumentRepository.find_one({"_id": document_id})
        if not document or not await DocumentService._can_read_full(document, current_user):
            raise HTTPException(status_code=403, detail="Bạn không có quyền giải mã tài liệu này")
        if redis:
            b64_key = await redis.get(f"aes_key:{document_id}:{user_id}")
            if b64_key:
                return {"key": b64_key.decode('utf-8') if isinstance(b64_key, bytes) else b64_key}
        raise HTTPException(status_code=403, detail="Khóa giải mã tài liệu không hợp lệ hoặc đã quá hạn sử dụng")

    @staticmethod
    @log_logic_execution
    async def get_document_preview(slug: str) -> dict:
        
        doc = await DocumentRepository.find_one(
            {
                "slug": slug,
                "status": DocumentStatus.PUBLISHED,
                "is_deleted": {"$ne": True},
                "visibility": "public",
            }
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")

        limit = doc.get("preview_pages", 5)
        raw_content = doc.get("content", "")
        preview_content = ""
        try:
            import json

            parsed = json.loads(raw_content)
            if "blocks" in parsed:
                parsed["blocks"] = parsed["blocks"][: limit * 5]
                preview_content = json.dumps(parsed)
            else:
                preview_content = raw_content[: limit * 1000]
        except (TypeError, ValueError, json.JSONDecodeError):
            preview_content = raw_content[: limit * 1000]

        preview_data = {
            "title": doc.get("title"),
            "description": doc.get("description"),
            "cover_url": doc.get("cover_url"),
            "creator_id": doc.get("creator_id"),
            "preview_content": preview_content,
        }
        return preview_data

    @staticmethod
    @log_logic_execution
    async def get_document_audit_logs(document_id: str, current_user) -> list:
        
        document = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}, projection={"_id": 1}
        )
        if not document:
            raise HTTPException(status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn")

        logs = (
            await mongo
            .find("audit_logs", {"document_id": document_id})
            .sort("timestamp", -1)
            .limit(100)
            .to_list(length=100)
        )
        return [
            {
                "_id": str(log["_id"]),
                "action": log.get("action"),
                "actor_id": log.get("actor_id"),
                "reason": log.get("reason"),
                "timestamp": (
                    log["timestamp"].isoformat()
                    if isinstance(log.get("timestamp"), datetime)
                    else log.get("timestamp")
                ),
            }
            for log in logs
        ]

    @staticmethod
    @log_logic_execution
    async def get_approval_queue(
        cursor: str = None,
        limit: int = 50,
    ) -> list:
        
        query = {"status": "processing_publish"}
        if cursor:
            import datetime as dt_mod

            query["updated_at"] = {
                "$gt": dt_mod.datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            }

        pipeline = [
            {"$match": query},
            {"$sort": {"updated_at": 1}},
            {"$limit": limit},
            {
                "$lookup": {
                    "from": "users",
                    "localField": "creator_id",
                    "foreignField": "_id",
                    "as": "author",
                }
            },
            {"$unwind": {"path": "$author", "preserveNullAndEmptyArrays": True}},
        ]

        documents = (
            await DocumentRepository
            .aggregate(pipeline)
            .to_list(length=limit)
        )

        def format_date(val):
            if isinstance(val, datetime):
                return val.isoformat()
            if isinstance(val, str):
                return val
            return datetime.now(timezone.utc).isoformat()

        return [
            {
                "_id": str(b["_id"]),
                "_id": str(b["_id"]),
                "title": b.get("title", ""),
                "description": b.get("description", ""),
                "creator_id": b.get("creator_id"),
                "author_name": b.get("author", {}).get("full_name", "Anonymous"),
                "created_at": format_date(b.get("created_at") or b.get("updated_at")),
                "updated_at": format_date(b.get("updated_at")),
                "submitted_at": format_date(b.get("updated_at")),
            }
            for b in documents
        ]

    @staticmethod
    @log_logic_execution
    async def get_trending_tags(
        limit: int = Query(
            default=20, le=100
        )
    ) -> List[str]:
        
        docs_col = DocumentRepository
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        results = await docs_col.aggregate(pipeline).to_list(length=None)
        return [r["_id"] for r in results]

    @staticmethod
    @log_logic_execution
    async def get_folders(parent_id: str, current_user):
        
        query = {"creator_id": str(current_user.id)}
        if parent_id:
            query["parent_id"] = parent_id
        cursor = mongo.query("workspace_folders").filter(query).sort("created_at", 1)
        folders = await cursor 
        for f in folders:
            f["_id"] = str(f["_id"])
        return folders

    @staticmethod
    @log_logic_execution
    async def create_folder(name: str, parent_id: str, current_user):
        
        folder_doc = {
            "name": name,
            "parent_id": parent_id,
            "creator_id": str(current_user.id),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        res = await mongo.insert_one(collection="workspace_folders", document=folder_doc)
        folder_doc["_id"] = str(res.inserted_id)
        return folder_doc

    @staticmethod
    @log_logic_execution
    async def delete_folder(folder_id: str, current_user):
        
        folder = await mongo.find_one(
            "workspace_folders", {"_id": folder_id, "creator_id": str(current_user.id)}
        )
        if not folder:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục làm việc")
        await mongo.delete_one("workspace_folders", {"_id": folder_id})
        await mongo.update_many(
            "documents", {"folder_id": folder_id}, {"$unset": {"folder_id": ""}}
        )
        return {"deleted": True}

    @staticmethod
    @log_logic_execution
    async def toggle_star_document(document_id: str, current_user):
        
        doc = await mongo.find_one(
            "documents", {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu trong kho chính"
            )
        current_starred = doc.get("is_starred", False)
        await mongo.update_one("documents", 
            {"_id": document_id}, {"$set": {"is_starred": not current_starred}}
        )
        return {"starred": not current_starred}

    @staticmethod
    @log_logic_execution
    async def transfer_document(document_id: str, new_owner_id: str, current_user):
        
        doc = await mongo.find_one("documents", 
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        target = None
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{settings.HUMANITY_URL}/nguoi-dung/{new_owner_id}",
                    headers={"X-Internal-Token": settings.SECRET_KEY},
                )
                if resp.status_code == 200:
                    target = resp.json().get("data")
        except Exception:
            logger.exception("Failed to verify ownership transfer target")
            raise HTTPException(status_code=503, detail="Dịch vụ hồ sơ người dùng tạm thời không khả dụng")
        if not target:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài khoản chuyển nhượng"
            )
        await mongo.update_one("documents", 
            {"_id": document_id},
            {
                "$set": {
                    "creator_id": new_owner_id,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return {"status": "transferred", "new_owner_id": new_owner_id}

    @staticmethod
    @log_logic_execution
    async def get_document_analytics(document_id: str, current_user):
        
        doc = await mongo.find_one(collection="documents", query={"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu trong kho chính"
            )
        if doc.get("creator_id") != str(current_user.id) and not DocumentService._is_admin(current_user):
            raise HTTPException(status_code=403, detail="Bạn không có quyền xem dữ liệu phân tích tài liệu này")
        views = doc.get("views", 0)
        content = doc.get("content", "")
        total_words = len(content.split()) if content else 0
        avg_read_time_min = max(1, total_words // 200)
        bookmark_count = await mongo.count_documents(collection="bookmarks", filter={"document_id": document_id})
        purchase_count = await database.mongodb[settings.FINANCE_DB_NAME].purchases.count_documents({"item_id": document_id, "status": "purchased"})
        return {
            "views": views,
            "avg_read_time": f"{avg_read_time_min} minutes",
            "avg_read_time_min": avg_read_time_min,
            "total_words": total_words,
            "saves": bookmark_count,
            "purchases": purchase_count,
        }

    @staticmethod
    @log_logic_execution
    async def get_document_academic(document_id: str, current_user):
        
        doc = await mongo.find_one(collection="documents", query={"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu trong kho chính"
            )
        if doc.get("creator_id") != str(current_user.id) and not DocumentService._is_admin(current_user) and doc.get("status") != DocumentStatus.PUBLISHED:
            raise HTTPException(status_code=403, detail="Bạn không có quyền xem chỉ số tài liệu này")
        content = doc.get("content", "")
        word_count = len(content.split()) if content else 0
        sentences = (
            content.count(".") + content.count("!") + content.count("?") if content else 0
        )
        avg_sentence_len = round(word_count / max(sentences, 1), 1)
        readability_score = max(0, min(100, 100 - (avg_sentence_len - 15) * 3))
        return {
            "word_count": word_count,
            "sentence_count": sentences,
            "avg_sentence_length": avg_sentence_len,
            "readability_score": round(readability_score, 1),
            "content_format": doc.get("content_format", "html"),
        }

    @staticmethod
    @log_logic_execution
    async def get_suggested_documents(
        limit: int = Query(
            default=20, le=100
        )
    ) -> List[dict]:
        
        docs_col = DocumentRepository
        cursor = docs_col.find({"status": "published", "is_deleted": {"$ne": True}, "visibility": "public"}).sort("views", -1).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [
            {
                "_id": str(b["_id"]),
                "slug": b.get("slug"),
                "title": b.get("title"),
                "author": b.get("author", "Unknown"),
                "cover_url": b.get("cover_url"),
                "mentions": b.get("views", 0),
            }
            for b in documents
        ]
