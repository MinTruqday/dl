import io
import json
import os
import uuid
import zipfile
from datetime import datetime, timezone
from typing import Any, List

from bson import ObjectId
from fastapi import HTTPException, Query, status
from loguru import logger
from passlib.context import CryptContext
from src.core.document_publication import trigger_document_publish_job
from src.schemas.document_metadata import (
    DocumentContentUpdate,
    DocumentCreate,
    DocumentInDB,
    DocumentStatus,
)
from uuid6 import uuid7

from core.infrastructure.app_config import settings
from core.infrastructure.database_client import db_client
from core.repositories.base_repository import RepositoryFactory
from core.file_storage import upload_file


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
    return document


class DocumentMetadata:
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
    async def get_tags_categories():
        db = db_client.mongodb.get_default_database()
        docs_col = RepositoryFactory.get("documents")
        pipeline_tags = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags"}},
            {"$sort": {"_id": 1}},
        ]
        pipeline_categories = [
            {"$unwind": "$categories"},
            {"$group": {"_id": "$categories"}},
            {"$sort": {"_id": 1}},
        ]
        tags_list = await docs_col.aggregate(pipeline_tags).to_list(100)
        categories_list = await docs_col.aggregate(pipeline_categories).to_list(100)
        return {
            "tags": [tag["_id"] for tag in tags_list],
            "categories": [category["_id"] for category in categories_list],
        }

    @staticmethod
    async def get_trending_documents(
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        )
    ) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        docs_col = RepositoryFactory.get("documents")
        cursor = (
            docs_col.find(
                {"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}}
            )
            .sort("views", -1)
            .limit(limit)
        )
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def get_text_search(
        query: str,
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        ),
    ) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        docs_col = RepositoryFactory.get("documents")
        cursor = docs_col.find(
            {
                "status": DocumentStatus.PUBLISHED,
                "is_deleted": {"$ne": True},
                "$text": {"$search": query},
            }
        ).limit(limit)
        documents = await cursor.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    async def create_document(doc_in: DocumentCreate, current_user):
        db = db_client.mongodb.get_default_database()
        docs_collection = RepositoryFactory.get("documents")
        existing_slug = await docs_collection.find_one({"slug": doc_in.slug})
        if existing_slug:
            raise HTTPException(
                status_code=400, detail="Đường dẫn định tuyến đã được sử dụng"
            )

        doc_dict = doc_in.model_dump()
        if not doc_dict.get("publisher_name"):
            doc_dict["publisher_name"] = current_user.full_name

        doc_doc = DocumentInDB(**doc_dict, creator_id=str(current_user.id))
        await docs_collection.insert_one(doc_doc.model_dump(by_alias=True))
        logger.info("Tạo tài liệu mới thành công")
        return doc_doc

    @staticmethod
    async def get_my_documents(
        current_user,
        q: str = None,
        cursor: str = None,
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        ),
    ) -> list:
        db = db_client.mongodb.get_default_database()
        query = {"creator_id": str(current_user.id), "is_deleted": {"$ne": True}}
        if q:
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
            ]
        if cursor:
            query["_id"] = {"$lt": cursor}

        docs = (
            await RepositoryFactory.get("documents")
            .find(query)
            .sort("_id", -1)
            .limit(limit)
            .to_list(length=limit)
        )
        return [
            {
                "_id": str(b["_id"]),
                "title": b.get("title", ""),
                "slug": b.get("slug", ""),
                "status": b.get("status", "draft"),
                "content_format": b.get("content_format", "json"),
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
    async def update_document_content(
        document_id: str, content_in: DocumentContentUpdate, current_user
    ):
        db = db_client.mongodb.get_default_database()
        docs_collection = RepositoryFactory.get("documents")
        document = await docs_collection.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

        if content_in.expected_version:
            db_updated = document.get("updated_at")
            if (
                db_updated
                and str(db_updated).split("+")[0]
                != str(content_in.expected_version).split("+")[0]
            ):
                raise HTTPException(
                    status_code=409,
                    detail="Không thể chỉnh sửa do đã có phiên bản mới hơn",
                )

        if document.get("content"):
            await RepositoryFactory.get("document_revisions").insert_one(
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
                import httpx

                async with httpx.AsyncClient() as client:
                    await client.post(
                        f"{settings.NOTIFICATION_URL}/thong-bao/kich-hoat",
                        json={
                            "target_user_id": str(current_user.id),
                            "title": "Document successfully updated",
                            "body": "The specified document content has been successfully synchronized and updated",
                            "type": "DOCUMENT_UPDATE",
                        },
                        timeout=settings.DEFAULT_HTTP_TIMEOUT,
                    )
            except Exception as e:
                logger.error("Lỗi gửi chuỗi thông báo cập nhật tài liệu")

        logger.info("Cập nhật nội dung tài liệu thành công")

        if hasattr(db_client, "redis") and db_client.redis:
            await db_client.redis.delete(f"document:{document_id}")
            if document.get("slug"):
                await db_client.redis.delete(f"document:slug:{document.get('slug')}")

        return serialize_document(await docs_collection.find_one({"_id": document_id}))

    @staticmethod
    async def update_document(document_id: str, doc_update, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        docs_col = RepositoryFactory.get("documents")
        doc = await docs_col.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        if (
            doc.get("creator_id") != str(current_user.id)
            and current_user.role != "ADMIN"
        ):
            raise HTTPException(
                status_code=403, detail="Không có quyền chỉnh sửa tài liệu"
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
                await RepositoryFactory.get("document_revisions").insert_one(
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

        if hasattr(db_client, "redis") and db_client.redis:
            await db_client.redis.delete(f"document:{document_id}")
            if doc.get("slug"):
                await db_client.redis.delete(f"document:slug:{doc.get('slug')}")

        return serialize_document(await docs_col.find_one({"_id": document_id}))

    @staticmethod
    async def list_documents(
        limit: int,
        cursor: str,
        q: str,
        sort_by: str,
        category: str = None,
        tag: str = None,
    ):
        db = db_client.mongodb.get_default_database()
        docs_collection = RepositoryFactory.get("documents")
        query = {"status": DocumentStatus.PUBLISHED, "is_deleted": {"$ne": True}}
        if q:
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
            ]
        if category:
            query["categories"] = category
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
    async def get_document_by_id(document_id: str, current_user, password: str = None):
        db = db_client.mongodb.get_default_database()
        docs_collection = RepositoryFactory.get("documents")
        user_id = str(current_user.id) if current_user else None

        document = await docs_collection.find_one({"_id": document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

        if (
            document.get("creator_id") != user_id
            and document.get("status") != DocumentStatus.PUBLISHED
        ):
            if not current_user or current_user.role != "ADMIN":
                raise HTTPException(
                    status_code=403, detail="Tài liệu đang ở trạng thái nháp"
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
            if hasattr(db_client, "redis") and db_client.redis:
                rl_key = f"rl:unlock:{document_id}:{user_id or 'guest'}"
                attempts = await db_client.redis.get(rl_key)
                if attempts and int(attempts) >= 5:
                    raise HTTPException(
                        status_code=429,
                        detail="Tạm khóa tài khoản do sai mật khẩu quá nhiều lần",
                    )

            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            if not pwd_context.verify(password, document.get("access_password_hash")):
                if rl_key and hasattr(db_client, "redis") and db_client.redis:
                    await db_client.redis.incr(rl_key)
                    await db_client.redis.expire(rl_key, 900)
                raise HTTPException(
                    status_code=403,
                    detail="Thông tin xác thực không khớp với hồ sơ bảo mật tài liệu",
                )

            if rl_key and hasattr(db_client, "redis") and db_client.redis:
                await db_client.redis.delete(rl_key)

        document = serialize_document(document)

        aes_key = None
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aes_key = AESGCM.generate_key(bit_length=256)
            import base64
            b64_key = base64.b64encode(aes_key).decode('utf-8')
            if hasattr(db_client, "redis") and db_client.redis:
                uid_str = user_id or "guest"
                await db_client.redis.setex(f"aes_key:{document['_id']}:{uid_str}", 300, b64_key)
        except ImportError:
            pass

        if document.get("content"):
            document["content_fragments"] = DocumentMetadata._fragment_document_content(document.get("content"), aes_key)
            del document["content"]

        return document

    @staticmethod
    async def soft_delete_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await RepositoryFactory.get("documents").update_one(
            {
                "_id": document_id,
                "creator_id": str(current_user.id),
                "is_deleted": {"$ne": True},
            },
            {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc)}},
        )
        if res.modified_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

        logger.info("Đã chuyển tài liệu vào thùng rác")
        return {"message": "Đã chuyển tài liệu vào thùng rác"}

    @staticmethod
    async def restore_document(document_id: str, current_user) -> dict:
        db = db_client.mongodb.get_default_database()
        res = await RepositoryFactory.get("documents").update_one(
            {
                "_id": document_id,
                "creator_id": str(current_user.id),
                "is_deleted": True,
            },
            {"$set": {"is_deleted": False, "deleted_at": None}},
        )
        if res.modified_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu trong thùng rác"
            )

        logger.info("Khôi phục tài liệu thành công")
        return {"message": "Khôi phục tài liệu từ thùng rác thành công"}

    @staticmethod
    async def get_trash(current_user) -> list:
        db = db_client.mongodb.get_default_database()
        docs = (
            await RepositoryFactory.get("documents")
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
    async def set_document_password(
        document_id: str, password: str, current_user
    ) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed = pwd_context.hash(password)
        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id},
            {
                "$set": {
                    "access_password_hash": hashed,
                    "is_password_protected": True,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Bật bảo vệ mật khẩu tài liệu thành công")
        return {"message": "Thiết lập mật khẩu tài liệu thành công"}

    @staticmethod
    async def invite_coauthor(document_id: str, email: str, current_user):
        db = db_client.mongodb.get_default_database()
        document = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

        import httpx

        target_user = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/email/{email}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    target_user = resp.json().get("data")
        except Exception as e:
            logger.warning("Lỗi đồng bộ thông tin tác giả")

        if not target_user:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài khoản với email này"
            )

        if str(target_user["_id"]) in document.get("coauthors", []):
            return {"message": "Tài khoản đã là cộng tác viên"}

        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id}, {"$addToSet": {"coauthors": str(target_user["_id"])}}
        )
        logger.info("Gửi lời mời cộng tác thành công")
        return {"message": "Bổ nhiệm cộng tác viên thành công"}

    @staticmethod
    async def get_document_by_slug(slug: str, current_user=None):
        db = db_client.mongodb.get_default_database()
        docs_collection = RepositoryFactory.get("documents")
        document = await docs_collection.find_one(
            {
                "slug": slug,
                "status": DocumentStatus.PUBLISHED,
                "is_deleted": {"$ne": True},
            }
        )
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

        user_id = str(current_user.id) if current_user else None
        has_purchased = False
        if user_id:
            if document.get("creator_id") == user_id:
                has_purchased = True
            else:
                purchases_col = RepositoryFactory.get("purchases")
                purchase = await purchases_col.find_one(
                    {"user_id": user_id, "item_id": str(document["_id"])}
                )
                if purchase:
                    has_purchased = True

        is_privileged = current_user and current_user.role == "ADMIN"
        if document.get("is_premium") and not has_purchased and not is_privileged:
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
            except:
                document["content"] = raw_content[: limit * 1000]

        should_increment = True
        if user_id == document.get("creator_id"):
            should_increment = False
        elif hasattr(db_client, "redis") and db_client.redis:
            cache_key = f"viewed:{user_id or 'guest'}:{document['_id']}"
            if await db_client.redis.get(cache_key):
                should_increment = False
            else:
                await db_client.redis.setex(cache_key, 600, "1")

        if should_increment:
            await docs_collection.update_one(
                {"_id": document["_id"]}, {"$inc": {"views": 1}}
            )
            document["views"] = document.get("views", 0) + 1
        document = serialize_document(document)

        import httpx

        author = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/{document['creator_id']}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    author = resp.json().get("data")
        except Exception as e:
            logger.warning("Lỗi đồng bộ hồ sơ tác giả")
        if author:
            document["author"] = {
                "full_name": author.get("full_name") or author.get("username"),
                "avatar_url": author.get("avatar_url"),
                "slug": author.get("slug"),
            }

        document["has_purchased"] = has_purchased
        aes_key = None
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            aes_key = AESGCM.generate_key(bit_length=256)
            import base64
            b64_key = base64.b64encode(aes_key).decode('utf-8')
            if hasattr(db_client, "redis") and db_client.redis:
                uid_str = user_id or "guest"
                await db_client.redis.setex(f"aes_key:{document['_id']}:{uid_str}", 300, b64_key)
        except ImportError:
            pass
        
        if document.get("content"):
            document["content_fragments"] = DocumentMetadata._fragment_document_content(document.get("content"), aes_key)
            del document["content"]
            
        return document

    @staticmethod
    async def get_document_decryption_key(document_id: str, current_user):
        user_id = str(current_user.id) if current_user else "guest"
        if hasattr(db_client, "redis") and db_client.redis:
            b64_key = await db_client.redis.get(f"aes_key:{document_id}:{user_id}")
            if b64_key:
                return {"key": b64_key.decode('utf-8') if isinstance(b64_key, bytes) else b64_key}
        raise HTTPException(status_code=403, detail="Khóa giải mã không tồn tại hoặc đã hết hạn")

    @staticmethod
    async def get_document_preview(slug: str) -> dict:
        db = db_client.mongodb.get_default_database()
        doc = await RepositoryFactory.get("documents").find_one(
            {
                "slug": slug,
                "status": DocumentStatus.PUBLISHED,
                "is_deleted": {"$ne": True},
            }
        )
        if not doc:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

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
        except:
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
    async def get_document_audit_logs(document_id: str, current_user) -> list:
        db = db_client.mongodb.get_default_database()
        document = await RepositoryFactory.get("documents").find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}, projection={"_id": 1}
        )
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")

        logs = (
            await RepositoryFactory.get("audit_logs")
            .find({"document_id": document_id})
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
                    if isinstance(log.get("timestamp"), datetime.datetime)
                    else log.get("timestamp")
                ),
            }
            for log in logs
        ]

    @staticmethod
    async def get_approval_queue(
        cursor: str = None,
        limit: int = 50,
        db=None,
    ) -> list:
        db = db_client.mongodb.get_default_database()
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
            await RepositoryFactory.get("documents")
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
    async def moderate_document(
        document_id: str, action: str, reason: str, current_user
    ) -> dict:
        db = db_client.mongodb.get_default_database()
        status_val = "PUBLISHED" if action == "approve" else "REJECTED"

        await RepositoryFactory.get("documents").update_one(
            {"_id": document_id},
            {
                "$set": {
                    "status": status_val,
                    "moderation_reason": reason,
                    "moderated_by": str(current_user.id),
                    "moderated_at": datetime.now(timezone.utc),
                }
            },
        )

        if action == "approve":
            doc = await RepositoryFactory.get("documents").find_one(
                {"_id": document_id}
            )
            if doc:
                await trigger_document_publish_job(document_id, doc.get("creator_id"))
                logger.info("Đã bắt đầu quy trình xuất bản")

        await RepositoryFactory.get("audit_logs").insert_one(
            {
                "action": f"DOCUMENT_{status_val}",
                "actor_id": str(current_user.id),
                "document_id": document_id,
                "reason": reason,
                "timestamp": datetime.now(timezone.utc),
            }
        )
        logger.info("Ghi nhận quyết định kiểm duyệt tài liệu thành công")
        return {"message": "Cập nhật trạng thái kiểm duyệt tài liệu thành công"}

    @staticmethod
    async def resolve_copyright_dispute(
        dispute_id: str, resolution: str, current_user
    ) -> dict:
        db = db_client.mongodb.get_default_database()
        await RepositoryFactory.get("copyright_disputes").update_one(
            {"_id": dispute_id},
            {
                "$set": {
                    "status": "resolved",
                    "resolution": resolution,
                    "resolved_by": str(current_user.id),
                    "resolved_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Giải quyết tranh chấp bản quyền thành công")
        return {"message": "Đã giải quyết tranh chấp bản quyền"}

    @staticmethod
    async def get_trending_tags(
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        )
    ) -> List[str]:
        db = db_client.mongodb.get_default_database()
        docs_col = RepositoryFactory.get("documents")
        pipeline = [
            {"$unwind": "$tags"},
            {"$group": {"_id": "$tags", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": limit},
        ]
        results = await docs_col.aggregate(pipeline).to_list(length=limit)
        return [r["_id"] for r in results]

    @staticmethod
    async def get_folders(parent_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        query = {"creator_id": str(current_user.id)}
        if parent_id:
            query["parent_id"] = parent_id
        cursor = db["workspace_folders"].find(query).sort("created_at", 1)
        folders = await cursor.to_list(length=100)
        for f in folders:
            f["_id"] = str(f["_id"])
        return folders

    @staticmethod
    async def create_folder(name: str, parent_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        folder_doc = {
            "name": name,
            "parent_id": parent_id,
            "creator_id": str(current_user.id),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        res = await db["workspace_folders"].insert_one(folder_doc)
        folder_doc["_id"] = str(res.inserted_id)
        return folder_doc

    @staticmethod
    async def delete_folder(folder_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        folder = await db["workspace_folders"].find_one(
            {"_id": folder_id, "creator_id": str(current_user.id)}
        )
        if not folder:
            raise HTTPException(status_code=404, detail="Không tìm thấy thư mục làm việc")
        await db["workspace_folders"].delete_one({"_id": folder_id})
        await db["documents"].update_many(
            {"folder_id": folder_id}, {"$unset": {"folder_id": ""}}
        )
        return {"deleted": True}

    @staticmethod
    async def toggle_star_document(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu trong kho chính"
            )
        current_starred = doc.get("is_starred", False)
        await db["documents"].update_one(
            {"_id": document_id}, {"$set": {"is_starred": not current_starred}}
        )
        return {"starred": not current_starred}

    @staticmethod
    async def transfer_document(document_id: str, new_owner_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Không tìm thấy tài liệu hoặc không có quyền truy cập",
            )
        import httpx

        target = None
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.MANAGEMENT_URL}/nguoi-dung/{new_owner_id}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    target = resp.json().get("data")
        except Exception:
            pass
        if not target:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài khoản chuyển nhượng"
            )
        await db["documents"].update_one(
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
    async def get_document_analytics(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu trong kho chính"
            )
        views = doc.get("views", 0)
        content = doc.get("content", "")
        total_words = len(content.split()) if content else 0
        avg_read_time_min = max(1, total_words // 200)
        bookmark_count = await db["bookmarks"].count_documents({"document_id": document_id})
        purchase_count = await db["transactions"].count_documents(
            {"reference_id": document_id, "type": {"$in": ["purchase", "receive"]}}
        )
        return {
            "views": views,
            "avg_read_time": f"{avg_read_time_min} minutes",
            "avg_read_time_min": avg_read_time_min,
            "total_words": total_words,
            "saves": bookmark_count,
            "purchases": purchase_count,
        }

    @staticmethod
    async def get_document_academic(document_id: str, current_user):
        db = db_client.mongodb.get_default_database()
        doc = await db["documents"].find_one({"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu trong kho chính"
            )
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
    async def get_suggested_documents(
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        )
    ) -> List[dict]:
        db = db_client.mongodb.get_default_database()
        docs_col = RepositoryFactory.get("documents")
        cursor = docs_col.find({"status": "published"}).sort("views", -1).limit(limit)
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
