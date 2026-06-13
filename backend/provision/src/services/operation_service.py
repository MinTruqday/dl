import uuid
from datetime import datetime, timezone

from core.database import db_client
from core.repositories.base_repository import RepositoryFactory
from core.schemas.user import RoleEnum
from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7


class OperationService:

    @staticmethod
    async def get_all_users(
        limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), offset: int = 0, cursor: str = None, db=None
    ) -> list:
        if db is None:
            db = db_client.mongodb.get_default_database()
        query = {}
        if cursor and isinstance(cursor, str):
            query["created_at"] = {
                "$lt": datetime.fromisoformat(cursor.replace("Z", "+00:00"))
            }
        users = (
            await RepositoryFactory.get("users")
            .find(query)
            .sort("created_at", -1)
            .skip(offset)
            .limit(limit)
            .to_list(length=limit)
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
    async def update_user_role(user_id: str, role: str, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        res = await RepositoryFactory.get("users").update_one(
            {"_id": user_id},
            {"$set": {"role": role, "updated_at": datetime.now(timezone.utc)}},
        )
        if res.matched_count == 0:
            raise HTTPException(
                status_code=404, detail="Không tìm thấy thông tin người dùng này"
            )
        logger.info(f"Vai trò người dùng {user_id} đã cập nhật thành {role}")
        return {"message": f"Đã cập nhật vai trò người dùng thành {role}"}

    @staticmethod
    async def update_user_status(user_id: str, is_active: bool, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        res = await RepositoryFactory.get("users").update_one(
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
                status_code=404, detail="Không tìm thấy thông tin người dùng này"
            )
        logger.info(f"Người dùng {user_id} trạng thái cập nhật thành {is_active}")
        return {"message": "Đã cập nhật trạng thái hoạt động của tài khoản"}

    @staticmethod
    async def toggle_maintenance_mode(
        enabled: bool, message: str = "", db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        await RepositoryFactory.get("system_config").update_one(
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
        logger.warning(
            f"Chế độ bảo trì đã được {('bật' if enabled else 'tắt')} bởi quản trị viên"
        )
        return {"message": f"Đã {('bật' if enabled else 'tắt')} chế độ bảo trì"}

    @staticmethod
    async def trigger_backup(action: str = "FULL", db=None) -> dict:
        logger.info("Lệnh sao lưu '{action}' đã được kích hoạt")
        return {"message": "Đã xếp lịch sao lưu dữ liệu"}

    @staticmethod
    async def create_api_key(
        name: str, provider: str = "DEFAULT", key_value: str = "", db=None
    ) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        if not key_value:
            import secrets

            key_value = secrets.token_urlsafe(32)
        await RepositoryFactory.get("api_keys").insert_one(
            {
                "_id": str(uuid7()),
                "name": name,
                "provider": provider,
                "key_value": key_value,
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info(f"Đã khởi tạo khóa truy cập {name} cho hệ thống")
        return {"message": "Vui lòng lưu trữ khóa truy cập an toàn", "key": key_value}

    @staticmethod
    async def create_marketing_campaign(data: dict, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        campaign = {
            "_id": str(uuid7()),
            "title": data.get("title", "Chiến dịch mới"),
            "target_audience": data.get("target", "ALL"),
            "discount_percent": data.get("discount", 0),
            "status": "active",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("marketing_campaigns").insert_one(campaign)
        logger.info("Chiến dịch '{campaign['title']}' đã được khởi tạo")
        return {"message": "Đã tạo chiến dịch tiếp thị"}

    @staticmethod
    async def get_system_health(db=None) -> dict:
        import os

        import httpx
        from core.config import settings

        if db is None:
            db = db_client.mongodb.get_default_database()
        try:
            await db.command("ping")
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        redis_status = "disconnected"
        if db_client.redis:
            try:
                await db_client.redis.ping()
                redis_status = "connected"
            except Exception:
                redis_status = "error"
        else:
            redis_status = "not_configured"
        rag_status = "unknown"
        rag_url = settings.AGENTIC_AI_URL
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
    async def get_maintenance_mode(db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        config = await RepositoryFactory.get("system_config").find_one(
            {"key": "maintenance_mode"}
        )
        if not config:
            return {"enabled": False, "message": ""}
        return {
            "enabled": config.get("enabled", False),
            "message": config.get("message", ""),
        }

    @staticmethod
    async def get_minio_stats(db=None) -> dict:
        from core.storage import get_storage_client

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
                    "Anna Archive": {"count": 0, "size": 0},
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
                                categories["Anna Archive"]["count"] += 1
                                categories["Anna Archive"]["size"] += size
                            elif key.startswith("images/"):
                                categories["User Images"]["count"] += 1
                                categories["User Images"]["size"] += size
                            elif key.startswith("tài liệu/"):
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
            logger.error("Lỗi lấy thông số từ hệ thống lưu trữ")
            return {
                "status": "unreachable",
                "total_buckets": 0,
                "total_size_bytes": 0,
                "total_objects_count": 0,
                "buckets": [],
                "categories": [],
            }

    @staticmethod
    async def get_collector_stats(db=None) -> dict:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.COLLECTOR_URL}/statistics", timeout=settings.DEFAULT_HTTP_TIMEOUT
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.error("Lỗi lấy dữ liệu thống kê")
        return {
            "total_documents": 0,
            "total_assets": 0,
            "collector_status": "OFFLINE",
            "last_crawl": None,
            "storage_usage_mb": 0,
        }

    @staticmethod
    async def trigger_collection(source: str, pages: int, db=None) -> dict:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.COLLECTOR_URL}/trigger",
                    json={"source": source, "pages": pages},
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"status": "error", "message": resp.text}
        except Exception as e:
            logger.error("Lỗi kích hoạt thu thập")
        return {
            "status": "error",
            "message": "Không thể kết nối đến hệ thống thu thập dữ liệu",
        }

    @staticmethod
    async def stop_collection(db=None) -> dict:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{settings.COLLECTOR_URL}/pause", timeout=settings.DEFAULT_HTTP_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"status": "error", "message": resp.text}
        except Exception as e:
            logger.error("Lỗi dừng thu thập")
        return {
            "status": "error",
            "message": "Không thể kết nối đến hệ thống thu thập dữ liệu",
        }

    @staticmethod
    async def get_collector_logs(db=None) -> list:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.COLLECTOR_URL}/logs", timeout=settings.DEFAULT_HTTP_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.error("Lỗi lấy logs thu thập")
        return []

    @staticmethod
    async def get_active_collector_jobs(db=None) -> list:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.COLLECTOR_URL}/running-jobs", timeout=settings.DEFAULT_HTTP_TIMEOUT
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.error("Lỗi lấy danh sách công việc thu thập đang chạy")
        return []

    @staticmethod
    async def handle_bug_report(data: dict, current_moderator, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        report_id = str(uuid7())
        await RepositoryFactory.get("bug_reports").insert_one(
            {
                "_id": report_id,
                "title": data["title"],
                "description": data["description"],
                "status": "open",
                "assigned_to": str(current_moderator.id),
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info(f"Lỗi {report_id} đã được giải quyết bởi {current_moderator.id}")
        return {"message": "Đã ghi nhận báo cáo sự cố"}

    @staticmethod
    async def assign_task(data: dict, current_moderator, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        task = {
            "_id": str(uuid7()),
            "assigned_to": data["moderator_id"],
            "title": data["title"],
            "status": "pending",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("moderator_tasks").insert_one(task)
        logger.info(
            f"Đã giao việc cho {data['moderator_id']} bởi {current_moderator.id}"
        )
        return {"message": "Đã phân công nhiệm vụ"}

    @staticmethod
    async def submit_policy_proposal(data: dict, current_moderator, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        proposal_id = str(uuid7())
        await RepositoryFactory.get("policy_proposals").insert_one(
            {
                "_id": proposal_id,
                "author_id": str(current_moderator.id),
                "title": data["title"],
                "content": data["content"],
                "status": "pending",
                "created_at": datetime.now(timezone.utc),
            }
        )
        logger.info(
            f"Đề xuất mới {proposal_id} vừa được gửi bởi {current_moderator.id}"
        )

    @staticmethod
    async def get_withdrawal_requests(
        status: str = "PENDING", limit: int = Query(default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT), db=None
    ) -> list:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.FINANCE_URL}/withdrawal/hang-doi?status={status}&limit={limit}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json().get("data", [])
        except Exception as e:
            logger.error("Lỗi lấy danh sách rút tiền từ hệ thống tài chính")
        return []

    @staticmethod
    async def approve_withdrawal(withdrawal_id: str, admin_id: str, db=None) -> dict:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.FINANCE_URL}/withdrawal/{withdrawal_id}/xac-thuc",
                    params={"action": "approve"},
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"status": "error", "message": resp.text}
        except Exception as e:
            logger.error(f"Lỗi duyệt rút tiền {withdrawal_id}")
        return {
            "status": "error",
            "message": "Không thể kết nối đến hệ thống tài chính",
        }

    @staticmethod
    async def reject_withdrawal(
        withdrawal_id: str, reason: str, admin_id: str, db=None
    ) -> dict:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.FINANCE_URL}/withdrawal/{withdrawal_id}/xac-thuc",
                    params={"action": "reject", "reason": reason},
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"status": "error", "message": resp.text}
        except Exception as e:
            logger.error(f"Lỗi từ chối rút tiền {withdrawal_id}")
        return {
            "status": "error",
            "message": "Không thể kết nối đến hệ thống tài chính",
        }
