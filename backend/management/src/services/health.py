from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.redis import redis
from src.core.infrastructure.mongo import mongo
import gzip
import os
import tempfile
import time
from datetime import datetime, timezone

import httpx
from bson import json_util
from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.repositories.system import SystemRepository
from src.repositories.policy import PolicyProposalRepository
from src.repositories.moderation import ModerationRepository
from src.services.humanity_client import HumanityClient

PROCESS_STARTED_AT = time.monotonic()

class HealthService:

    @staticmethod
    @log_logic_execution
    async def get_all_users(
        limit: int = Query(
            default=20, le=100
        ),
        offset: int = 0,
        cursor: str = None,
    ) -> list:
        return await HumanityClient.list(limit, offset) or []

    @staticmethod
    @log_logic_execution
    async def update_user_role(user_id: str, role: str) -> dict:
        await HumanityClient.update(user_id, {"role": role})
        logger.info("Account access privileges updated")
        return {"message": "Cập nhật quyền truy cập hệ thống hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def update_user_status(user_id: str, is_active: bool) -> dict:
        await HumanityClient.update(user_id, {"is_active": is_active})
        logger.info("Account status updated")
        return {"message": "Cập nhật trạng thái hoạt động tài khoản hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def toggle_maintenance_mode(
        enabled: bool, message: str = ""
    ) -> dict:
        await SystemRepository.update_config(
            {"key": "maintenance_mode"},
            {
                "$set": {
                    "enabled": enabled,
                    "message": message,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )
        logger.warning("System maintenance mode toggled")
        return {"message": "Cập nhật cấu hình bảo trì hệ thống hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def trigger_backup() -> dict:
        from src.core.storage import upload_file_path

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        backup_id = str(uuid7())
        object_name = f"system/backups/doclib-{timestamp}-{backup_id}.json.gz"
        created_at = datetime.now(timezone.utc)
        await mongo.insert_one(
            "backup_jobs",
            {
                "_id": backup_id,
                "object_name": object_name,
                "size_bytes": 0,
                "document_count": 0,
                "status": "running",
                "created_at": created_at,
            },
        )
        file_path = ""
        try:
            with tempfile.NamedTemporaryFile(
                prefix="doclib-backup-",
                suffix=".json.gz",
                delete=False,
            ) as temporary:
                file_path = temporary.name
            document_count = 0
            with gzip.open(file_path, "wt", encoding="utf-8", compresslevel=6) as output:
                output.write('{"created_at":')
                output.write(json_util.dumps(created_at))
                output.write(',"databases":{')
                database_index = 0
                names = await database.mongodb.list_database_names()
                for database_name in names:
                    if database_name in {"admin", "config", "local"}:
                        continue
                    if database_index:
                        output.write(",")
                    database_index += 1
                    output.write(json_util.dumps(database_name))
                    output.write(":{")
                    target = database.mongodb[database_name]
                    collection_index = 0
                    for collection_name in await target.list_collection_names():
                        if collection_index:
                            output.write(",")
                        collection_index += 1
                        output.write(json_util.dumps(collection_name))
                        output.write(":[")
                        document_index = 0
                        async for document in target[collection_name].find({}).batch_size(250):
                            if document_index:
                                output.write(",")
                            document_index += 1
                            document_count += 1
                            output.write(json_util.dumps(document))
                        output.write("]")
                    output.write("}")
                output.write("}}")
            size_bytes = os.path.getsize(file_path)
            await upload_file_path(
                file_path,
                object_name,
                content_type="application/gzip",
            )
            await mongo.update_one(
                "backup_jobs",
                {"_id": backup_id},
                {
                    "$set": {
                        "size_bytes": size_bytes,
                        "document_count": document_count,
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc),
                    }
                },
            )
            logger.info("System data backup completed")
            return {
                "object_name": object_name,
                "size_bytes": size_bytes,
                "document_count": document_count,
                "status": "completed",
            }
        except Exception:
            await mongo.update_one(
                "backup_jobs",
                {"_id": backup_id},
                {
                    "$set": {
                        "status": "failed",
                        "completed_at": datetime.now(timezone.utc),
                    }
                },
            )
            logger.exception("System data backup failed")
            raise HTTPException(
                status_code=503,
                detail="Không thể hoàn thành bản sao lưu dữ liệu hệ thống",
            )
        finally:
            if file_path and os.path.exists(file_path):
                os.unlink(file_path)

    @staticmethod
    @log_logic_execution
    async def get_system_health() -> dict:
        import os

        from src.core.infrastructure.configuration import settings as shared_settings

        try:
            await mongo.get_db().command("ping")
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        redis_status = "disconnected"
        try:
            await redis.ping()
            redis_status = "connected"
        except Exception:
            redis_status = "error"
        rag_status = "unknown"
        rag_url = shared_settings.AGENTIC_AI_URL
        if rag_url:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"{rag_url}/ready")
                    rag_status = "healthy" if resp.status_code == 200 else "degraded"
            except Exception:
                rag_status = "unreachable"
        load_avg = os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]
        cpu_count = os.cpu_count() or 1
        cpu_usage = f"{min(load_avg[0] / cpu_count * 100, 100):.1f}%"
        return {
            "status": (
                "healthy"
                if db_status == "connected"
                and redis_status == "connected"
                and (rag_status == "healthy")
                else "degraded"
            ),
            "services": {
                "database": db_status,
                "cache": redis_status,
                "ai_agent": rag_status,
            },
            "resources": {
                "cpu_load": cpu_usage,
                "uptime_seconds": int(time.monotonic() - PROCESS_STARTED_AT),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    @log_logic_execution
    async def get_maintenance_mode() -> dict:
        config = await SystemRepository.find_config(
            {"key": "maintenance_mode"}
        )
        if not config:
            return {"enabled": False, "message": ""}
        return {
            "enabled": config.get("enabled", False),
            "message": config.get("message", ""),
        }

    @staticmethod
    @log_logic_execution
    async def get_minio_stats() -> dict:
        from src.core.storage import get_storage_client

        try:
            storage_client = await get_storage_client()
            buckets_resp = await storage_client.list_buckets()
            buckets_list = buckets_resp.get("Buckets", [])
            total_size_bytes = 0
            total_objects_count = 0
            buckets_data = []
            categories = {
                "CTAN": {"count": 0, "size": 0},
                "NXBGD": {"count": 0, "size": 0},
                "NXBST": {"count": 0, "size": 0},
                "AnnaSource Archive": {"count": 0, "size": 0},
                "User Images": {"count": 0, "size": 0},
                "User Documents": {"count": 0, "size": 0},
                "Others": {"count": 0, "size": 0},
            }
            for b in buckets_list:
                bucket_name = b["Name"]
                paginator = storage_client.get_paginator("list_objects_v2")
                obj_count = 0
                bucket_size = 0
                async for page in paginator.paginate(Bucket=bucket_name):
                    for obj in page.get("Contents", []):
                        size = obj["Size"]
                        key = obj["Key"]
                        bucket_size += size
                        obj_count += 1
                        total_size_bytes += size
                        total_objects_count += 1
                        if "ctan" in key.lower():
                            category = "CTAN"
                        elif "nxbgd" in key.lower():
                            category = "NXBGD"
                        elif "nxbst" in key.lower():
                            category = "NXBST"
                        elif "anna_archive" in key.lower():
                            category = "AnnaSource Archive"
                        elif key.startswith("images/"):
                            category = "User Images"
                        elif key.startswith("documents/"):
                            category = "User Documents"
                        else:
                            category = "Others"
                        categories[category]["count"] += 1
                        categories[category]["size"] += size
                buckets_data.append(
                    {
                        "name": bucket_name,
                        "created_at": b["CreationDate"].isoformat() if "CreationDate" in b else "",
                        "size_bytes": bucket_size,
                        "objects_count": obj_count,
                    }
                )
            formatted_categories = []
            for name, stats in categories.items():
                if stats["count"] > 0 or stats["size"] > 0:
                    formatted_categories.append(
                        {"name": name, "count": stats["count"], "size_bytes": stats["size"]}
                    )
            return {
                "status": "healthy",
                "total_buckets": len(buckets_list),
                "total_size_bytes": total_size_bytes,
                "total_objects_count": total_objects_count,
                "buckets": buckets_data,
                "categories": formatted_categories,
            }
        except Exception:
            logger.exception("Failed to retrieve storage statistics due to connection failure")
            return {
                "status": "unreachable",
                "total_buckets": 0,
                "total_size_bytes": 0,
                "total_objects_count": 0,
                "buckets": [],
                "categories": [],
            }

    @staticmethod
    @log_logic_execution
    async def handle_bug_report(data: dict, current_user) -> dict:
        report_id = str(uuid7())
        await ModerationRepository.insert_bug_report(
            {
                "_id": report_id,
                "title": data["title"],
                "description": data["description"],
                "status": "open",
                "assigned_to": str(current_user.id),
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info("Bug report recorded")
        return {"message": "Báo cáo sự cố hệ thống đã được ghi nhận hoàn tất"}

    @staticmethod
    @log_logic_execution
    async def submit_policy_proposal(data: dict, current_user) -> dict:
        proposal_id = str(uuid7())
        await PolicyProposalRepository.insert_one(
            {
                "_id": proposal_id,
                "creator_id": str(current_user.id),
                "title": data["title"],
                "content": data["content"],
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info("Policy proposal submitted")


    @staticmethod
    @log_logic_execution
    async def update_shadowban(user_id: str, status: bool, current_user) -> dict:
        await HumanityClient.update(user_id, {"is_shadowbanned": status})
        await HealthService._audit(current_user, "user.shadowban", user_id, {"status": status})
        return {"user_id": user_id, "is_shadowbanned": status}

    @staticmethod
    @log_logic_execution
    async def update_kyc(user_id: str, status: str, current_user) -> dict:
        normalized = status.upper()
        if normalized not in {"PENDING", "VERIFIED", "REJECTED"}:
            raise HTTPException(status_code=422, detail="Trạng thái xác minh không hợp lệ")
        now = datetime.now(timezone.utc)
        values = {"kyc_status": normalized, "updated_at": now}
        if normalized == "VERIFIED":
            values["kyc_verified_at"] = now
        await HumanityClient.update(user_id, values)
        await HealthService._audit(current_user, "user.kyc", user_id, {"status": normalized})
        return {"user_id": user_id, "kyc_status": normalized}

    @staticmethod
    async def get_system_config() -> dict:
        result = {"registration_enabled": True}
        async for row in mongo.find("system_config", {}):
            if row.get("key") == "maintenance_mode":
                result["maintenance_enabled"] = row.get("enabled", False)
                result["maintenance_message"] = row.get("message", "")
            elif row.get("key") == "registration_enabled":
                result["registration_enabled"] = row.get("value", True)
        return result

    @staticmethod
    async def update_system_config(values: dict, current_user) -> dict:
        if "registration_enabled" in values:
            await mongo.update_one("system_config", {"key": "registration_enabled"}, {"$set": {"value": values["registration_enabled"], "updated_at": datetime.now(timezone.utc)}}, upsert=True)
        await HealthService._audit(current_user, "system.config", "system", values)
        return await HealthService.get_system_config()

    @staticmethod
    async def get_admin_reports() -> list:
        rows = await mongo.find("reports", {}, sort=[("created_at", -1)], limit=100).to_list(length=100)
        result = []
        for row in rows:
            item = dict(row)
            item["_id"] = str(item.get("_id", ""))
            if isinstance(item.get("created_at"), datetime):
                item["created_at"] = item["created_at"].isoformat()
            result.append(item)
        return result

    @staticmethod
    async def update_admin_report(report_id: str, status: str, current_user) -> dict:
        now = datetime.now(timezone.utc)
        result = await ModerationRepository.update_report(
            {"_id": report_id},
            {"$set": {"status": status, "resolved_at": now, "resolved_by": str(current_user.id)}},
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo yêu cầu")
        await HealthService._audit(current_user, "report.update", report_id, {"status": status})
        return {"report_id": report_id, "status": status}

    @staticmethod
    async def _audit(current_user, action: str, target_id: str, details: dict):
        await SystemRepository.insert_audit_log({"_id": str(uuid7()), "actor_id": str(current_user.id), "action": action, "target_id": target_id, "details": details, "timestamp": datetime.now(timezone.utc)})
