import io
import json
import os
import uuid
import zipfile
import hashlib
import base64
import re
import unicodedata
from datetime import datetime, timezone
from typing import Any, List

import httpx
from bson import ObjectId
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from fastapi import HTTPException, Query, status
from loguru import logger
from passlib.context import CryptContext

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.redis import redis
from src.core.logic_logger import log_logic_execution
from src.core.publication import trigger_document_publish_job
from src.repositories.document import DocumentRepository
from src.schemas.document import DocumentContentUpdate, DocumentCreate, DocumentInDB, DocumentStatus
from src.services.drm_client import DrmClient
from src.services.finance_client import FinanceClient
from src.services.document.base import (
    serialize_document,
    is_admin,
    get_effective_collaboration_status,
    has_purchase,
    can_read_full,
    pwd_context,
)

class DocumentCrudService:
    @staticmethod
    @log_logic_execution
    async def create_document(doc_in: DocumentCreate, current_user):
        slug = doc_in.slug
        if not slug:
            normalized = (
                unicodedata.normalize("NFKD", doc_in.title)
                .encode("ascii", "ignore")
                .decode("ascii")
                .lower()
            )
            slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-") or "tai-lieu"
        existing_slug = await DocumentRepository.find_one({"slug": slug})
        if existing_slug:
            slug = f"{slug}-{uuid.uuid4().hex[:8]}"

        doc_dict = doc_in.model_dump(exclude={"password"})
        doc_dict["slug"] = slug
        if not doc_dict.get("publisher_name"):
            doc_dict["publisher_name"] = current_user.full_name

        doc_doc = DocumentInDB(**doc_dict, creator_id=str(current_user.id))
        doc_data = doc_doc.model_dump()
        doc_data["views"] = 0
        doc_data["reads_count"] = 0
        doc_data["is_deleted"] = False
        doc_data["coauthors"] = []
        doc_data["invited_users"] = []
        doc_data["created_at"] = datetime.now(timezone.utc)
        doc_data["updated_at"] = datetime.now(timezone.utc)

        if doc_in.password:
            doc_data["access_password_hash"] = pwd_context.hash(doc_in.password)
            doc_data["is_password_protected"] = True

        result = await DocumentRepository.insert_one(doc_data)
        doc_data["_id"] = result.inserted_id

        if doc_data.get("status") == DocumentStatus.PUBLISHED:
            try:
                await trigger_document_publish_job(doc_data["_id"])
            except Exception:
                logger.exception("Publish event notification failed")

        return serialize_document(doc_data)

    @staticmethod
    @log_logic_execution
    async def import_document_from_file(file, current_user) -> dict:
        content_bytes = await file.read()
        if len(content_bytes) < 60:
            raise ValueError("Tệp tin không hợp lệ hoặc bị hỏng")

        file_id_bytes = content_bytes[:16]
        file_hash = content_bytes[16:48]
        nonce = content_bytes[48:60]
        ciphertext = content_bytes[60:]

        file_id = str(uuid.UUID(bytes=file_id_bytes))

        license_doc = await DrmClient.license_by_file(file_id)
        if not license_doc:
            raise ValueError("Không tìm thấy giấy phép hợp lệ cho tài liệu này")
        if license_doc.get("status") != "ACTIVE":
            raise ValueError("Giấy phép tài liệu đã hết hiệu lực")
        if license_doc.get("user_id") != str(current_user.id) and not is_admin(current_user):
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

        doc_in = DocumentCreate(
            title=file.filename.split(".")[0] if file.filename else "Imported Document",
            content=raw_content,
            content_format=content_format,
        )
        return await DocumentCrudService.create_document(doc_in, current_user)

    @staticmethod
    @log_logic_execution
    async def get_my_documents(
        current_user,
        status_filter: str = None,
        sort_by: str = "updated_at",
        limit: int = 50,
        cursor: str = None,
        folder_id: str = None,
    ):
        user_id = str(current_user.id)
        query = {
            "$or": [{"creator_id": user_id}, {"coauthors": user_id}],
            "is_deleted": {"$ne": True},
        }
        if status_filter:
            query["status"] = status_filter
        if folder_id:
            query["folder_id"] = folder_id

        sort_mapping = {
            "latest": ("created_at", -1),
            "updated_at": ("updated_at", -1),
            "views": ("views", -1),
            "title": ("title", 1),
        }
        sort_field, sort_dir = sort_mapping.get(sort_by, ("updated_at", -1))
        if cursor:
            query["_id"] = {"$lt": cursor}

        cursor_db = DocumentRepository.find(query).sort(sort_field, sort_dir).limit(limit)
        documents = await cursor_db.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    @log_logic_execution
    async def update_document_content(
        document_id: str,
        update_data: DocumentContentUpdate,
        current_user,
    ):
        document = await DocumentRepository.find_one({"_id": document_id})
        if not document:
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )

        user_id = str(current_user.id)
        is_coauthor = user_id in document.get("coauthors", [])
        is_creator = document.get("creator_id") == user_id

        status_info = get_effective_collaboration_status(
            document, user_id=user_id, is_adm=is_admin(current_user)
        )
        if not status_info["can_edit"]:
            raise HTTPException(
                status_code=403,
                detail="Tài liệu đã đóng chế độ chỉnh sửa hoặc bạn không có quyền cập nhật",
            )

        if not is_creator and not is_coauthor and not is_admin(current_user):
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền chỉnh sửa nội dung tài liệu này",
            )

        new_content = update_data.content
        word_count = len(new_content.split())
        reading_time_min = max(1, word_count // 200)

        update_dict = {
            "content": new_content,
            "reading_time_minutes": reading_time_min,
            "word_count": word_count,
            "updated_at": datetime.now(timezone.utc),
            "last_modified_by": user_id,
        }

        await DocumentRepository.update_one({"_id": document_id}, {"$set": update_dict})
        updated = await DocumentRepository.find_one({"_id": document_id})
        return serialize_document(updated)

    @staticmethod
    @log_logic_execution
    async def update_document(document_id: str, doc_update, current_user) -> dict:
        document = await DocumentRepository.find_one({"_id": document_id})
        if not document:
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )

        user_id = str(current_user.id)
        is_coauthor = user_id in document.get("coauthors", [])
        is_creator = document.get("creator_id") == user_id

        if not is_creator and not is_coauthor and not is_admin(current_user):
            raise HTTPException(
                status_code=403,
                detail="Bạn không có quyền cập nhật thông tin tài liệu này",
            )

        update_data = (
            doc_update.model_dump(exclude_unset=True)
            if hasattr(doc_update, "model_dump")
            else dict(doc_update)
        )
        update_data["updated_at"] = datetime.now(timezone.utc)

        if "password" in update_data:
            pwd = update_data.pop("password")
            if pwd:
                update_data["access_password_hash"] = pwd_context.hash(pwd)
                update_data["is_password_protected"] = True
            else:
                update_data["access_password_hash"] = None
                update_data["is_password_protected"] = False

        await DocumentRepository.update_one({"_id": document_id}, {"$set": update_data})
        updated = await DocumentRepository.find_one({"_id": document_id})
        return serialize_document(updated)

    @staticmethod
    @log_logic_execution
    async def list_documents(
        limit: int, cursor: str, q: str, sort_by: str, category: str = None, tag: str = None
    ):
        query = {
            "status": DocumentStatus.PUBLISHED,
            "is_deleted": {"$ne": True},
            "visibility": "public",
            "drm_settings.hide_from_search": {"$ne": True},
        }
        if q:
            query["$or"] = [
                {"title": {"$regex": q, "$options": "i"}},
                {"description": {"$regex": q, "$options": "i"}},
            ]
        if category:
            query["category"] = category
        if tag:
            query["tags"] = tag

        sort_mapping = {"latest": ("created_at", -1), "views": ("views", -1)}
        sort_field, sort_dir = sort_mapping.get(sort_by, ("created_at", -1))

        if cursor:
            if sort_field == "created_at":
                query["_id"] = {"$lt": cursor}

        cursor_db = DocumentRepository.find(query).sort(sort_field, sort_dir).limit(limit)
        documents = await cursor_db.to_list(length=limit)
        return [serialize_document(d) for d in documents]

    @staticmethod
    @log_logic_execution
    async def get_document_by_id(
        document_id: str, current_user, password: str = None, share_token: str | None = None
    ):
        user_id = str(current_user.id) if current_user else None
        document = await DocumentRepository.find_one({"_id": document_id})
        if not document:
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )

        is_coauthor = user_id in document.get("coauthors", [])
        is_creator = document.get("creator_id") == user_id

        status_info = get_effective_collaboration_status(
            document, user_id=user_id, is_adm=is_admin(current_user)
        )
        if not status_info["can_view"] and not is_creator and not is_admin(current_user):
            raise HTTPException(
                status_code=403,
                detail="Tài liệu đã đóng hoàn toàn hoặc đã hết thời hạn cho phép truy cập",
            )

        if (
            document.get("is_deleted") is True
            and not is_creator
            and not is_coauthor
            and not is_admin(current_user)
        ):
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )

        if document.get("is_password_protected"):
            if not is_creator and not is_coauthor and not is_admin(current_user):
                hashed = document.get("access_password_hash")
                if not password or not pwd_context.verify(password, hashed):
                    raise HTTPException(
                        status_code=401,
                        detail="Tài liệu được bảo vệ bằng mật khẩu truy cập",
                    )

        can_view_full_content = await can_read_full(document, current_user)
        serialized = serialize_document(document)
        serialized["can_read_full"] = can_view_full_content
        if not can_view_full_content:
            raw_content = serialized.get("content", "")
            serialized["content"] = raw_content[:500] if raw_content else ""
            serialized["is_truncated"] = True

        return serialized

    @staticmethod
    @log_logic_execution
    async def get_document_by_slug(slug: str, current_user=None):
        document = await DocumentRepository.find_one({"slug": slug})
        if not document:
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )
        return await DocumentCrudService.get_document_by_id(str(document["_id"]), current_user)

    @staticmethod
    @log_logic_execution
    async def soft_delete_document(document_id: str, current_user) -> dict:
        res = await DocumentRepository.update_one(
            {"_id": document_id, "creator_id": str(current_user.id), "is_deleted": {"$ne": True}},
            {"$set": {"is_deleted": True, "deleted_at": datetime.now(timezone.utc)}},
        )
        if res.modified_count == 0:
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )
        logger.info("Document moved to recycle bin")
        return {"message": "Tài liệu đã được di chuyển vào thùng rác hệ thống"}

    @staticmethod
    @log_logic_execution
    async def restore_document(document_id: str, current_user) -> dict:
        res = await DocumentRepository.update_one(
            {"_id": document_id, "creator_id": str(current_user.id), "is_deleted": True},
            {"$set": {"is_deleted": False, "deleted_at": None}},
        )
        if res.modified_count == 0:
            raise HTTPException(
                status_code=404, detail="Hệ thống không tìm thấy tài liệu yêu cầu trong thùng rác"
            )
        logger.info("Document restored from recycle bin")
        return {"message": "Tài liệu đã được khôi phục hoàn tất từ thùng rác"}

    @staticmethod
    @log_logic_execution
    async def get_trash(current_user) -> list:
        docs = await (
            DocumentRepository.find({"creator_id": str(current_user.id), "is_deleted": True})
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
    async def set_document_password(document_id: str, password: str, current_user) -> dict:
        doc = await DocumentRepository.find_one(
            {"_id": document_id, "creator_id": str(current_user.id)}
        )
        if not doc:
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )
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
        logger.info("Document password protection enabled")
        return {"message": "Thiết lập mật khẩu bảo vệ tài liệu hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def get_document_decryption_key(document_id: str, current_user):
        doc = await DocumentRepository.find_one({"_id": document_id})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )
        user_id = str(current_user.id)
        if doc.get("creator_id") != user_id and not is_admin(current_user):
            can_read = await can_read_full(doc, current_user)
            if not can_read:
                raise HTTPException(status_code=403, detail="Bạn không có quyền lấy khóa giải mã")
        return {"document_id": document_id, "key": doc.get("encryption_key", "")}

    @staticmethod
    @log_logic_execution
    async def get_document_preview(slug: str) -> dict:
        doc = await DocumentRepository.find_one({"slug": slug})
        if not doc:
            raise HTTPException(
                status_code=404, detail="Hệ thống không thể tìm thấy tài liệu theo yêu cầu của bạn"
            )
        return {
            "title": doc.get("title"),
            "description": doc.get("description"),
            "cover_url": doc.get("cover_url"),
            "author": doc.get("publisher_name") or doc.get("author", "Unknown"),
            "views": doc.get("views", 0),
            "preview_snippet": (doc.get("content", "")[:300] if doc.get("content") else ""),
        }
