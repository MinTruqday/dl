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

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

def is_admin(current_user) -> bool:
    role = getattr(current_user, "role", "") if current_user else ""
    from src.core.dependency import Role
    return str(getattr(role, "value", role)).lower() == Role.ADMIN.value

def get_effective_collaboration_status(document: dict, user_id: str | None = None, is_adm: bool = False) -> dict:
    if not document:
        return {
            "mode": "CLOSED",
            "effective_mode": "CLOSED",
            "is_effective_closed": True,
            "is_read_only": True,
            "can_edit": False,
            "can_comment": False,
            "closed_reason": "document_not_found",
            "closed_at": None,
            "closed_by": None,
        }
    setting = document.get("collaboration_setting") or {}
    mode = str(setting.get("mode") or "CLOSED").upper()
    owner_id = str(document.get("user_id") or "")
    co_authors = [str(x) for x in (document.get("co_authors") or [])]
    is_author_or_coauthor = bool(user_id and (user_id == owner_id or user_id in co_authors))
    closed_at = setting.get("closed_at")
    closed_by = setting.get("closed_by")
    closed_reason = setting.get("closed_reason")
    if mode == "CLOSED":
        return {
            "mode": mode,
            "effective_mode": "CLOSED",
            "is_effective_closed": True,
            "is_read_only": True,
            "can_edit": bool(is_adm or is_author_or_coauthor),
            "can_comment": False,
            "closed_reason": closed_reason or "explicitly_closed",
            "closed_at": closed_at,
            "closed_by": closed_by,
        }
    auto_close_at = setting.get("auto_close_at")
    if auto_close_at:
        try:
            if isinstance(auto_close_at, str):
                auto_close_dt = datetime.fromisoformat(auto_close_at.replace("Z", "+00:00"))
            else:
                auto_close_dt = auto_close_at
            if datetime.now(timezone.utc) >= auto_close_dt:
                return {
                    "mode": mode,
                    "effective_mode": "CLOSED",
                    "is_effective_closed": True,
                    "is_read_only": True,
                    "can_edit": bool(is_adm or is_author_or_coauthor),
                    "can_comment": False,
                    "closed_reason": "auto_close_expired",
                    "closed_at": auto_close_dt.isoformat(),
                    "closed_by": "system",
                }
        except Exception:
            pass
    max_collaborators = int(setting.get("max_collaborators") or 0)
    current_collaborators = len(document.get("co_authors") or [])
    if max_collaborators > 0 and current_collaborators >= max_collaborators:
        return {
            "mode": mode,
            "effective_mode": "CLOSED",
            "is_effective_closed": True,
            "is_read_only": True,
            "can_edit": bool(is_adm or is_author_or_coauthor),
            "can_comment": False,
            "closed_reason": "max_collaborators_reached",
            "closed_at": closed_at,
            "closed_by": closed_by,
        }
    return {
        "mode": mode,
        "effective_mode": mode,
        "is_effective_closed": False,
        "is_read_only": False,
        "can_edit": bool(is_adm or is_author_or_coauthor or mode == "PUBLIC_EDIT"),
        "can_comment": bool(is_adm or is_author_or_coauthor or mode in {"PUBLIC_EDIT", "PUBLIC_COMMENT"}),
        "closed_reason": None,
        "closed_at": None,
        "closed_by": None,
    }

async def has_purchase(user_id: str | None, document_id: str) -> bool:
    if not user_id or not document_id:
        return False
    return await FinanceClient.has_purchased(user_id, document_id)

async def can_read_full(document: dict, current_user) -> bool:
    if not document:
        return False
    if is_admin(current_user):
        return True
    user_id = str(current_user.id) if current_user else None
    owner_id = str(document.get("user_id", ""))
    if user_id and user_id == owner_id:
        return True
    if user_id and user_id in [str(c) for c in document.get("co_authors", [])]:
        return True
    access_type = document.get("access_type", "PUBLIC")
    if access_type == "PUBLIC":
        return True
    if access_type == "PRIVATE":
        return bool(user_id and user_id == owner_id)
    if access_type == "RESTRICTED":
        return bool(user_id and user_id in [str(u) for u in document.get("allowed_users", [])])
    if access_type == "PAID":
        price = float(document.get("price") or 0)
        if price <= 0:
            return True
        return await has_purchase(user_id, str(document.get("_id", "")))
    return False
