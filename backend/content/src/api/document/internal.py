import re
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pymongo import ReturnDocument

from src.core.dependency import verify_internal_token
from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.logging_route import LoggingRoute
from src.services.document.base import can_read_full

router = APIRouter(route_class=LoggingRoute)


def normalize_internal_query(value: Any) -> Any:
    """Accept serialized Mongo ObjectIds from other services.

    Public APIs expose every document id as a string. Older collected documents,
    however, still store ``_id`` as an ObjectId. Internal callers must therefore
    be able to address either representation without knowing how the document was
    originally created.
    """
    if isinstance(value, list):
        return [normalize_internal_query(item) for item in value]
    if not isinstance(value, dict):
        return value

    normalized: dict[str, Any] = {}
    for key, item in value.items():
        if key == "_id" and isinstance(item, str) and ObjectId.is_valid(item):
            normalized[key] = {"$in": [item, ObjectId(item)]}
        else:
            normalized[key] = normalize_internal_query(item)
    return normalized


def serialize_internal(value: Any):
    if isinstance(value, dict):
        return {key: serialize_internal(item) for key, item in value.items()}
    if isinstance(value, list):
        return [serialize_internal(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


@router.post(
    "/noi-bo/tai-lieu", dependencies=[Depends(verify_internal_token)], include_in_schema=False
)
async def internal_document_data(req: dict):
    operation = str(req.get("operation", ""))
    query = normalize_internal_query(req.get("query") or {})
    projection = req.get("projection")
    documents = database.mongodb[settings.CONTENT_DB_NAME].documents
    if operation == "find_one":
        document = await documents.find_one(query, projection)
        return {"data": serialize_internal(document)}
    if operation == "find_many":
        limit = min(max(int(req.get("limit") or 100), 1), 200)
        cursor = documents.find(query, projection)
        sort = req.get("sort") or []
        if sort:
            cursor = cursor.sort([(str(field), int(direction)) for field, direction in sort])
        rows = await cursor.limit(limit).to_list(length=limit)
        return {"data": serialize_internal(rows)}
    if operation == "update_one":
        result = await documents.update_one(
            query,
            req.get("update") or {},
            upsert=bool(req.get("upsert", False)),
        )
        return {
            "data": {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None,
            }
        }
    if operation == "taxonomy":
        rows = await documents.aggregate(
            [
                {
                    "$match": {
                        "status": "published",
                        "visibility": "public",
                        "is_deleted": {"$ne": True},
                    }
                },
                {
                    "$group": {
                        "_id": None,
                        "categories": {"$addToSet": "$category"},
                        "tags": {"$push": "$tags"},
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "categories": 1,
                        "tags": {
                            "$reduce": {
                                "input": "$tags",
                                "initialValue": [],
                                "in": {
                                    "$setUnion": [
                                        "$$value",
                                        {"$ifNull": ["$$this", []]},
                                    ]
                                },
                            }
                        },
                    }
                },
            ]
        ).to_list(length=1)
        data = rows[0] if rows else {"categories": [], "tags": []}
        data["categories"] = sorted(
            value for value in data.get("categories", []) if value
        )
        data["tags"] = sorted(value for value in data.get("tags", []) if value)
        return {"data": data}
    raise HTTPException(status_code=422, detail="Thao tác dữ liệu nội bộ không hợp lệ")


@router.post(
    "/noi-bo/truy-cap", dependencies=[Depends(verify_internal_token)], include_in_schema=False
)
async def get_internal_document(req: dict):
    document_id = str(req.get("document_id", ""))
    user_id = str(req.get("user_id", ""))
    edit = bool(req.get("edit", False))
    is_admin = bool(req.get("is_admin", False))
    document = await database.mongodb[settings.CONTENT_DB_NAME].documents.find_one(
        {"_id": document_id, "is_deleted": {"$ne": True}}
    )
    if document and edit and not is_admin:
        can_edit = user_id == document.get("creator_id") or user_id in document.get(
            "coauthors", []
        )
        if not can_edit:
            document = None
    elif document and not edit:
        from types import SimpleNamespace

        current_user = SimpleNamespace(
            id=user_id,
            role="admin" if is_admin else "reader",
        )
        if not await can_read_full(document, current_user):
            document = None
    if not document:
        raise HTTPException(
            status_code=404, detail="Không tìm thấy tài liệu hoặc thiếu quyền truy cập"
        )
    return {"data": serialize_internal(document)}


@router.post(
    "/noi-bo/cong-viec", dependencies=[Depends(verify_internal_token)], include_in_schema=False
)
async def update_document_job(req: dict):
    action = str(req.get("action", ""))
    document_id = str(req.get("document_id", ""))
    creator_id = str(req.get("creator_id", ""))
    job_id = str(req.get("job_id", ""))
    now = datetime.now(timezone.utc)
    documents = database.mongodb[settings.CONTENT_DB_NAME].documents
    if action == "get_creator":
        row = await documents.find_one({"_id": document_id}, {"creator_id": 1})
        return {"data": {"exists": bool(row), "creator_id": str((row or {}).get("creator_id", ""))}}
    if action == "compile_complete":
        result = await documents.update_one(
            {"_id": document_id, "creator_id": creator_id},
            {
                "$set": {
                    "compiled_file_url": req["file_url"],
                    "compile_status": "completed",
                    "compiled_at": now,
                    "updated_at": now,
                },
                "$unset": {"compile_error": ""},
            },
        )
        return {"data": {"updated": result.modified_count == 1}}
    if action == "publish_complete":
        result = await documents.update_one(
            {
                "_id": document_id,
                "creator_id": creator_id,
                "publication_job_id": job_id,
                "status": "processing_publish",
                "is_deleted": {"$ne": True},
            },
            {
                "$set": {"status": "published", "published_at": now, "updated_at": now},
                "$unset": {
                    "publication_job_id": "",
                    "publication_error": "",
                    "scheduled_publish_at": "",
                    "publish_at": "",
                },
            },
        )
        current = await documents.find_one({"_id": document_id}, {"status": 1})
        return {
            "data": {"updated": result.modified_count == 1, "status": (current or {}).get("status")}
        }
    if action == "compile_failed":
        await documents.update_one(
            {"_id": document_id},
            {
                "$set": {
                    "compile_status": "failed",
                    "compile_error": str(req.get("error", ""))[-1000:],
                    "updated_at": now,
                }
            },
        )
        return {"data": {"updated": True}}
    if action == "publish_failed":
        await documents.update_one(
            {"_id": document_id, "publication_job_id": job_id, "status": "processing_publish"},
            {
                "$set": {
                    "status": "draft",
                    "publication_error": str(req.get("error", ""))[-1000:],
                    "updated_at": now,
                },
                "$unset": {"publication_job_id": "", "scheduled_publish_at": "", "publish_at": ""},
            },
        )
        return {"data": {"updated": True}}
    if action == "claim_scheduled":
        row = await documents.find_one_and_update(
            {
                "scheduled_publish_at": {"$lte": now},
                "status": {"$nin": ["processing_publish", "published"]},
                "is_deleted": {"$ne": True},
                "creator_id": {"$type": "string"},
            },
            {
                "$set": {
                    "status": "processing_publish",
                    "publication_job_id": job_id,
                    "updated_at": now,
                }
            },
            return_document=ReturnDocument.AFTER,
        )
        return {
            "data": None
            if not row
            else {"document_id": str(row["_id"]), "creator_id": str(row["creator_id"])}
        }
    if action == "release_scheduled":
        await documents.update_one(
            {"_id": document_id, "publication_job_id": job_id},
            {"$set": {"status": "draft", "updated_at": now}, "$unset": {"publication_job_id": ""}},
        )
        return {"data": {"updated": True}}
    raise HTTPException(status_code=422, detail="Tác vụ tài liệu nội bộ không hợp lệ")


@router.post(
    "/noi-bo/thong-ke", dependencies=[Depends(verify_internal_token)], include_in_schema=False
)
async def get_internal_document_stats(req: dict):
    documents = database.mongodb[settings.CONTENT_DB_NAME].documents
    source_ids = [str(value) for value in req.get("source_ids", [])]
    source_names = [str(value) for value in req.get("source_names", [])]
    total_documents = await documents.count_documents({"is_deleted": {"$ne": True}})
    result = {"total_documents": total_documents}
    if source_ids or source_names:
        collected_filter = {"$or": []}
        if source_ids:
            collected_filter["$or"].append({"creator_id": {"$in": source_ids}})
        if source_names:
            collected_filter["$or"].append({"source_name": {"$in": source_names}})
        result["total_assets"] = await documents.count_documents(
            {"$or": [{"file_url": {"$type": "string"}}, {"pdf_url": {"$type": "string"}}]}
        )
        result["total_collected"] = await documents.count_documents(collected_filter)
        recent = (
            await documents.find(collected_filter, {"created_at": 1})
            .sort("created_at", -1)
            .limit(1)
            .to_list(length=1)
        )
        result["last_run"] = recent[0].get("created_at") if recent else None
    return {"data": result}


@router.post(
    "/noi-bo/trao-doi", dependencies=[Depends(verify_internal_token)], include_in_schema=False
)
async def exchange_internal_document(req: dict):
    action = str(req.get("action", ""))
    document_id = str(req.get("document_id", ""))
    documents = database.mongodb[settings.CONTENT_DB_NAME].documents
    if action == "get_document":
        document = await documents.find_one({"_id": document_id, "is_deleted": {"$ne": True}})
        if not document:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        document["_id"] = str(document["_id"])
        document.pop("password", None)
        document.pop("access_password_hash", None)
        return {"data": document}
    if action == "get_accessible_document":
        user_id = str(req.get("user_id", ""))
        is_admin = bool(req.get("is_admin", False))
        edit = bool(req.get("edit", False))
        access = [
            {"creator_id": user_id},
            {"coauthors": user_id},
            {"collaborators.user_id": user_id},
            {"shared_with.user_id": user_id},
        ]
        if not edit:
            access.append({"visibility": "public", "status": "published"})
        query = {"_id": document_id, "is_deleted": {"$ne": True}}
        if not is_admin:
            query["$or"] = access
        document = await documents.find_one(query)
        if not document:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu hoặc thiếu quyền truy cập"
            )
        document["_id"] = str(document["_id"])
        document.pop("password", None)
        document.pop("access_password_hash", None)
        return {"data": document}
    if action == "list_creator_documents":
        creator_id = str(req.get("creator_id", ""))
        rows = await documents.find(
            {"creator_id": creator_id, "is_deleted": {"$ne": True}},
            {"title": 1, "slug": 1, "views": 1, "view_count": 1, "price_dl": 1, "price_dls": 1},
        ).to_list(length=None)
        for row in rows:
            row["_id"] = str(row["_id"])
        return {"data": rows}
    if action == "list_analytics_documents":
        creator_id = str(req.get("creator_id") or "").strip()
        search = str(req.get("search") or "").strip()
        query = {"status": "published", "is_deleted": {"$ne": True}}
        if creator_id:
            query["creator_id"] = creator_id
        if search:
            query["title"] = {"$regex": re.escape(search), "$options": "i"}
        rows = await documents.find(
            query,
            {
                "title": 1,
                "slug": 1,
                "views": 1,
                "view_count": 1,
                "price_dl": 1,
                "price_dls": 1,
                "is_drm_protected": 1,
                "creator_id": 1,
                "created_at": 1,
            },
        ).to_list(length=None)
        for row in rows:
            row["_id"] = str(row["_id"])
        return {"data": rows}
    if action == "update_pricing":
        actor_id = str(req.get("actor_id", ""))
        is_admin = bool(req.get("is_admin", False))
        query = {"_id": document_id, "is_deleted": {"$ne": True}}
        if not is_admin:
            query["creator_id"] = actor_id
        values = {
            "price_dl": max(0, int(req.get("price_dl", 0))),
            "is_drm_protected": bool(req.get("is_drm_protected", True)),
            "is_premium": int(req.get("price_dl", 0)) > 0,
            "updated_at": datetime.now(timezone.utc),
        }
        result = await documents.update_one(query, {"$set": values})
        if result.matched_count != 1:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy tài liệu hoặc thiếu quyền cập nhật"
            )
        return {"data": {"document_id": document_id, **values}}
    if action == "update_index":
        result = await documents.update_one(
            {"_id": document_id, "is_deleted": {"$ne": True}},
            {
                "$set": {
                    "indexing_status": "indexed",
                    "indexed_chunks": int(req.get("indexed_chunks", 0)),
                    "extraction_method": str(req.get("extraction_method", "")),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return {"data": {"updated": result.matched_count == 1}}
    if action == "update_drm_policy":
        allowed = {
            "disable_copy",
            "disable_print",
            "hide_from_search",
            "watermark_enabled",
            "allow_internal_ai",
            "license_valid_days",
            "max_open_count",
            "ghost_font_enabled",
            "ghost_font_exemption_scope",
            "ghost_font_exempt_user_ids",
            "protection_tier",
        }
        values = {
            key: value for key, value in dict(req.get("values") or {}).items() if key in allowed
        }
        result = await documents.update_one(
            {"_id": document_id, "is_deleted": {"$ne": True}},
            {"$set": {"drm_settings": values, "updated_at": datetime.now(timezone.utc)}},
        )
        if result.matched_count != 1:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        return {"data": {"document_id": document_id, "drm_settings": values}}
    if action == "upsert_collected":
        payload = dict(req.get("document") or {})
        identity = payload.get("source_url") or payload.get("file_url")
        if not identity:
            raise HTTPException(status_code=422, detail="Tài liệu thu thập thiếu định danh nguồn")
        now = datetime.now(timezone.utc)
        payload.setdefault("_id", str(uuid.uuid4()))
        payload.setdefault("created_at", now)
        payload["updated_at"] = now
        query = {"source_url": identity} if payload.get("source_url") else {"file_url": identity}
        row = await documents.find_one_and_update(
            query, {"$setOnInsert": payload}, upsert=True, return_document=ReturnDocument.AFTER
        )
        collected_doc_id = str(row["_id"])
        if payload.get("file_url"):
            import asyncio
            async def _fire_collected_ingest():
                try:
                    async with httpx.AsyncClient(timeout=5.0) as client:
                        await client.post(
                            f"{settings.AGENTIC_AI_URL}/su-kien/webhook/tai-lieu-dang-tai",
                            params={"document_id": collected_doc_id, "user_id": ""},
                            headers={"X-Internal-Token": settings.SECRET_KEY},
                        )
                except Exception:
                    logger.warning(f"Collected document ingest webhook failed for document_id={collected_doc_id}")
            asyncio.create_task(_fire_collected_ingest())
        return {"data": {"document_id": collected_doc_id}}
    if action == "update_collected":
        result = await documents.update_one(
            {"_id": document_id},
            {"$set": {**dict(req.get("values") or {}), "updated_at": datetime.now(timezone.utc)}},
        )
        return {"data": {"updated": result.modified_count == 1}}
    if action == "auto_save_draft":
        result = await documents.update_one(
            {"_id": document_id, "is_deleted": {"$ne": True}},
            {
                "$set": {
                    "draft_content": dict(req.get("content") or {}),
                    "toc": list(req.get("toc") or []),
                    "reading_time_minutes": max(1, int(req.get("reading_time_minutes", 1))),
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        return {"data": {"updated": result.matched_count == 1}}
    if action == "submit_for_review":
        result = await documents.update_one(
            {
                "_id": document_id,
                "status": {"$nin": ["pending_review", "published"]},
                "is_deleted": {"$ne": True},
            },
            {"$set": {"status": "pending_review", "updated_at": datetime.now(timezone.utc)}},
        )
        return {"data": {"updated": result.modified_count == 1}}
    if action == "global_find_replace":
        current = await documents.find_one(
            {"_id": document_id, "is_deleted": {"$ne": True}}, {"_id": 1}
        )
        if not current:
            raise HTTPException(status_code=404, detail="Không tìm thấy tài liệu")
        now = datetime.now(timezone.utc)
        await database.mongodb[settings.CONTENT_DB_NAME].document_versions.insert_one(
            {
                "_id": str(uuid.uuid4()),
                "document_id": document_id,
                "creator_id": str(req.get("creator_id", "")),
                "note": "Tìm và thay thế",
                "snapshot": dict(req.get("snapshot") or {}),
                "created_at": now,
            }
        )
        values = dict(req.get("update") or {})
        values["updated_at"] = now
        await documents.update_one({"_id": document_id}, {"$set": values})
        return {"data": {"updated": True}}
    if action == "get_versions":
        version_ids = [str(value) for value in req.get("version_ids", [])]
        object_ids = [ObjectId(value) for value in version_ids if ObjectId.is_valid(value)]
        rows = (
            await database.mongodb[settings.CONTENT_DB_NAME]
            .document_versions.find(
                {"document_id": document_id, "_id": {"$in": version_ids + object_ids}}
            )
            .limit(len(version_ids))
            .to_list(length=len(version_ids))
        )
        for row in rows:
            row["_id"] = str(row["_id"])
        return {"data": rows}
    if action == "search_documents":
        text = str(req.get("query", "")).strip()
        search_filter = {
            "status": "published",
            "is_deleted": {"$ne": True},
            "drm_settings.hide_from_search": {"$ne": True},
        }
        if text:
            search_filter["$or"] = [
                {"title": {"$regex": text, "$options": "i"}},
                {"description": {"$regex": text, "$options": "i"}},
                {"tags": {"$regex": text, "$options": "i"}},
            ]
        rows = await documents.find(search_filter).limit(3).to_list(length=3)
        if not rows and text:
            rows = (
                await documents.find(
                    {
                        "status": "published",
                        "is_deleted": {"$ne": True},
                        "drm_settings.hide_from_search": {"$ne": True},
                    }
                )
                .limit(3)
                .to_list(length=3)
            )
        result = []
        for row in rows:
            result.append(
                {
                    "id": str(row["_id"]),
                    "title": row.get("title", ""),
                    "slug": row.get("slug", ""),
                    "price_dl": row.get("price_dl", 0),
                    "summary": row.get("summary") or row.get("description") or "",
                }
            )
        return {"data": result}
    raise HTTPException(status_code=422, detail="Tác vụ trao đổi tài liệu không hợp lệ")
