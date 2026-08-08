import io
import json
import os
import uuid
import zipfile
import base64
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
            "can_view": False,
            "closed_reason": "document_not_found",
            "closed_at": None,
            "closed_by": None,
        }
    creator_id = str(document.get("creator_id") or "")
    if is_adm or (user_id and str(user_id) == creator_id):
        return {
            "mode": document.get("collaboration_mode", "OPEN"),
            "effective_mode": "OPEN",
            "is_effective_closed": False,
            "is_read_only": False,
            "can_edit": True,
            "can_comment": True,
            "can_view": True,
            "closed_reason": None,
            "closed_at": None,
            "closed_by": None,
        }
    schedules = document.get("collaboration_schedules") or []
    active_schedules = [item for item in schedules if item.get("is_active", True)]
    effective_mode = None
    if active_schedules:
        now = datetime.now(timezone.utc)
        in_window_rule = None
        for rule in active_schedules:
            start_at = rule.get("start_at")
            end_at = rule.get("end_at")
            if isinstance(start_at, str):
                try:
                    start_at = datetime.fromisoformat(start_at.replace("Z", "+00:00"))
                except ValueError:
                    start_at = None
            elif isinstance(start_at, datetime) and start_at.tzinfo is None:
                start_at = start_at.replace(tzinfo=timezone.utc)
            if isinstance(end_at, str):
                try:
                    end_at = datetime.fromisoformat(end_at.replace("Z", "+00:00"))
                except ValueError:
                    end_at = None
            elif isinstance(end_at, datetime) and end_at.tzinfo is None:
                end_at = end_at.replace(tzinfo=timezone.utc)
            if end_at and ((start_at and start_at <= now <= end_at) or (not start_at and now <= end_at)):
                in_window_rule = rule
                break
        if in_window_rule:
            effective_mode = str(in_window_rule.get("mode") or "EDIT").upper()
        else:
            effective_mode = str(
                next(
                    (
                        item.get("fallback_mode")
                        for item in reversed(active_schedules)
                        if item.get("fallback_mode")
                    ),
                    "READ_ONLY",
                )
            ).upper()
    if not effective_mode:
        effective_mode = str(document.get("collaboration_mode") or "OPEN").upper()
    can_view = effective_mode != "CLOSED"
    can_comment = effective_mode in {"OPEN", "COMMENT", "COMMENT_ONLY", "EDIT"}
    can_edit = effective_mode in {"OPEN", "EDIT"}
    return {
        "mode": document.get("collaboration_mode", "OPEN"),
        "effective_mode": effective_mode,
        "is_effective_closed": effective_mode == "CLOSED",
        "is_read_only": effective_mode in {"READ_ONLY", "VIEW"},
        "can_edit": can_edit,
        "can_comment": can_comment,
        "can_view": can_view,
        "closed_reason": "explicitly_closed" if effective_mode == "CLOSED" else None,
        "closed_at": None,
        "closed_by": None,
    }

async def has_purchase(user_id: str | None, document_id: str) -> bool:
    if not user_id or not document_id:
        return False
    return await FinanceClient.has_purchase(user_id, document_id)

async def can_read_full(document: dict, current_user) -> bool:
    if not document:
        return False
    user_id = str(current_user.id) if current_user else None
    if (
        user_id == document.get("creator_id")
        or is_admin(current_user)
        or (user_id and user_id in document.get("coauthors", []))
    ):
        return True
    if document.get("status") != DocumentStatus.PUBLISHED or document.get("is_deleted") is True:
        return False
    if document.get("visibility", "public") != "public":
        return False
    if int(document.get("price_dl", 0) or 0) <= 0 and not document.get("is_premium"):
        return True
    return await has_purchase(user_id, str(document["_id"]))

def fragment_document_content(content: str, key: bytes | None = None) -> list[str]:
    if not content:
        return []
    if key:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM

        cipher = AESGCM(key)
        fragments = []
        for index in range(0, len(content), 50000):
            nonce = os.urandom(12)
            encrypted = cipher.encrypt(nonce, content[index : index + 50000].encode("utf-8"), None)
            fragments.append(base64.b64encode(nonce + encrypted).decode("utf-8"))
        return fragments
    return [
        base64.b64encode(content[index : index + 50].encode("utf-8")).decode("utf-8")
        for index in range(0, len(content), 50)
    ]
