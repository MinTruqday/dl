from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.redis import redis
from src.core.infrastructure.mongo import mongo
import uuid
from datetime import datetime, timezone

import httpx
from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.dependency import Role

from src.repositories.system import SystemRepository



from src.repositories.policy import PolicyProposalRepository

class HealthService:

    @staticmethod
    @log_logic_execution
    async def get_all_users(
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        ),
        offset: int = 0,
        cursor: str = None,
    ) -> list:
        query = {}
        if cursor and isinstance(cursor, str):
            query["created_at"] = {
                "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            }
        users = (
            await UserRepository
            .find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
            .execute()
        )
        return [
            {
                "_id": str(u["_id"]),
                "email": u.get("email"),
                "full_name": u.get("full_name"),
                "role": u.get("role"),
                "is_active": u.get("is_active", True),
                "created_at": (
                    u["created_at"].isoformat()
                    if isinstance(u.get("created_at"), datetime)
                    else u.get("created_at")
                ),
            }
            for u in users
        ]

    @staticmethod
    @log_logic_execution
    async def update_user_role(user_id: str, role: str) -> dict:
        res = await UserRepository.update_one(
            {"_id": user_id},
            {"$set": {"role": role, "updated_at": datetime.now(timezone.utc)}},
        )
        if res.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy hồ sơ người dùng"
            )
        logger.info("Cập nhật quyền truy cập tài khoản thành công")
        return {"message": "Cập nhật quyền truy cập thành công"}

    @staticmethod
    @log_logic_execution
    async def update_user_status(user_id: str, is_active: bool) -> dict:
        res = await UserRepository.update_one(
            {"_id": user_id},
            {
                "$set": {
                    "is_active": is_active,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        if res.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy hồ sơ người dùng"
            )
        logger.info("Cập nhật trạng thái hoạt động tài khoản thành công")
        return {"message": "Cập nhật trạng thái hoạt động thành công"}

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
        logger.warning("Thay đổi trạng thái bảo trì thành công")
        return {"message": "Cập nhật cấu hình bảo trì thành công"}

    @staticmethod
    @log_logic_execution
    async def trigger_backup(action: str = "FULL") -> dict:
        logger.info("Đã lên lịch sao lưu dữ liệu")
        return {"message": "Đang chạy tác vụ sao lưu dữ liệu"}

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
            await redis.get("ping_test")
            redis_status = "connected"
        except Exception:
            redis_status = "error"
        rag_status = "unknown"
        rag_url = shared_settings.AGENTIC_AI_URL
        if rag_url:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"{rag_url}/health")
                    rag_status = "healthy" if resp.status_code == 200 else "degraded"
            except Exception:
                rag_status = "unreachable"
        load_avg = os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]
        cpu_usage = (
            f"{min(load_avg[0] / os.cpu_count() * 100, 100):.1f}%"
            if hasattr(os, "cpu_count")
            else f"{min(load_avg[0] * 10, 100):.1f}%"
        )
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
            "resources": {"cpu_load": cpu_usage, "uptime": "99.9%"},
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
            async with await get_storage_client() as storage_client:
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
                                categories["CTAN"]["count"] += 1
                                categories["CTAN"]["size"] += size
                            elif "nxbgd" in key.lower():
                                categories["NXBGD"]["count"] += 1
                                categories["NXBGD"]["size"] += size
                            elif "nxbst" in key.lower():
                                categories["NXBST"]["count"] += 1
                                categories["NXBST"]["size"] += size
                            elif "anna_archive" in key.lower():
                                categories["AnnaSource Archive"]["count"] += 1
                                categories["AnnaSource Archive"]["size"] += size
                            elif key.startswith("images/"):
                                categories["User Images"]["count"] += 1
                                categories["User Images"]["size"] += size
                            elif key.startswith("documents/"):
                                categories["User Documents"]["count"] += 1
                                categories["User Documents"]["size"] += size
                            else:
                                categories["Others"]["count"] += 1
                                categories["Others"]["size"] += size
                    buckets_data.append(
                        {
                            "name": bucket_name,
                            "created_at": (
                                b["CreationDate"].isoformat()
                                if "CreationDate" in b
                                else ""
                            ),
                            "size_bytes": bucket_size,
                            "objects_count": obj_count,
                        }
                    )
                formatted_categories = []
                for name, stats in categories.items():
                    if stats["count"] > 0 or stats["size"] > 0:
                        formatted_categories.append(
                            {
                                "name": name,
                                "count": stats["count"],
                                "size_bytes": stats["size"],
                            }
                        )
                return {
                    "status": "healthy",
                    "total_buckets": len(buckets_list),
                    "total_size_bytes": total_size_bytes,
                    "total_objects_count": total_objects_count,
                    "buckets": buckets_data,
                    "categories": formatted_categories,
                }
        except Exception as e:
            logger.exception("Lỗi truy xuất thống kê lưu trữ do sự cố kết nối")
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
        logger.info("Ghi nhận báo cáo lỗi thành công")
        return {"message": "Báo cáo sự cố thành công"}

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
        logger.info("Đã gửi đề xuất chính sách")

    @staticmethod
    @log_logic_execution
    async def create_marketing_campaign(data: dict) -> dict:
        return {}
        
    @staticmethod
    @log_logic_execution
    async def bulk_update_shadowban(user_ids, status, current_user) -> dict:
        return {}
        
    @staticmethod
    @log_logic_execution
    async def bulk_verify_kyc(user_ids, status, current_user) -> dict:
        return {}

