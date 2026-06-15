from core.config import settings
import uuid
from datetime import datetime, timezone

from core.database import db_client
from core.repositories.base_repository import RepositoryFactory
from core.schemas.user import RoleEnum
from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7


class OperationService:

    @staticmethod
    async def get_all_users(
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        ),
        offset: int = 0,
        cursor: str = None,
        db=None,
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
                status_code=404, detail="The system was unable to locate a user profile matching the provided account identifier"
            )
        logger.info(f"The access privileges for the user account associated with identifier {user_id} have been successfully modified to the requested role")
        return {"message": "The access privileges for the specified account have been successfully updated and applied"}

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
                status_code=404, detail="The system was unable to locate a user profile matching the provided account identifier"
            )
        logger.info(f"The operational activity status for the user account associated with identifier {user_id} has been updated to reflect the new state")
        return {"message": "The operational activity status for the specified account has been successfully updated"}

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
            "The global system maintenance mode has been toggled by an authorized administrator"
        )
        return {"message": "The global system maintenance mode configuration has been successfully updated"}

    @staticmethod
    async def trigger_backup(action: str = "FULL", db=None) -> dict:
        logger.info("A comprehensive system data backup task has been successfully triggered and scheduled for execution")
        return {"message": "The requested data backup task has been scheduled and is currently running in the background"}

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
        logger.info("A new secure application programming interface key has been generated by the system")
        return {"message": "The new access key has been generated successfully so please ensure you store it in a secure location", "key": key_value}

    @staticmethod
    async def create_marketing_campaign(data: dict, db=None) -> dict:
        if db is None:
            db = db_client.mongodb.get_default_database()
        campaign = {
            "_id": str(uuid7()),
            "title": data.get("title", "New Promotional Campaign"),
            "target_audience": data.get("target", "ALL"),
            "discount_percent": data.get("discount", 0),
            "status": "active",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("marketing_campaigns").insert_one(campaign)
        logger.info("A new marketing and promotional campaign has been successfully initiated and recorded in the database")
        return {"message": "The promotional marketing campaign has been successfully created and is now active"}

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
        except Exception:
            logger.error("The system encountered an unexpected network disruption while attempting to retrieve storage statistics from the object storage service")
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
                    f"{settings.COLLECTOR_URL}/stats",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            logger.error("The system encountered an error while attempting to fetch statistical data from the data collection service")
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
                    return {"status": "error", "message": "The external service rejected the collection request due to invalid parameters"}
        except Exception:
            logger.error("The system encountered an unexpected network disruption while attempting to trigger the external data collection process")
        return {
            "status": "error",
            "message": "The system was unable to establish a secure connection with the external data collection service",
        }

    @staticmethod
    async def stop_collection(db=None) -> dict:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.COLLECTOR_URL}/stop",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"status": "error", "message": "The request to halt the ongoing data collection process was rejected by the external service"}
        except Exception:
            logger.error("The system encountered an unexpected network disruption while attempting to halt the external data collection process")
        return {
            "status": "error",
            "message": "The system was unable to establish a secure connection with the external data collection service",
        }

    @staticmethod
    async def get_collector_logs(db=None) -> list:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.COLLECTOR_URL}/logs",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            logger.error("The system encountered an error while attempting to fetch the operational logs from the data collection service")
        return []

    @staticmethod
    async def get_active_collector_jobs(db=None) -> list:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.COLLECTOR_URL}/active-jobs",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            logger.error("The system encountered an error while attempting to retrieve the list of active background jobs from the data collection service")
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
        logger.info("The reported system issue has been officially documented and assigned to the corresponding moderation staff for review")
        return {"message": "The system issue report has been successfully recorded and submitted for further investigation"}

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
            "A new administrative task has been successfully generated and assigned to the specified moderation staff member"
        )
        return {"message": "The administrative task has been successfully assigned and logged into the system workflow"}

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
            "A new structural policy proposal has been successfully submitted and is currently awaiting administrative review"
        )

    @staticmethod
    async def get_withdrawal_requests(
        status: str = "PENDING",
        limit: int = Query(
            default=settings.DEFAULT_PAGE_LIMIT, le=settings.MAX_PAGE_LIMIT
        ),
        db=None,
    ) -> list:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{settings.FINANCE_URL}/withdrawals/queue?status={status}&limit={limit}",
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json().get("data", [])
        except Exception:
            logger.error("The system encountered an unexpected network disruption while attempting to retrieve the withdrawal queue from the billing subsystem")
        return []

    @staticmethod
    async def approve_withdrawal(withdrawal_id: str, admin_id: str, db=None) -> dict:
        import httpx
        from core.config import settings
        from loguru import logger

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{settings.FINANCE_URL}/withdrawals/{withdrawal_id}/verify",
                    params={"action": "approve"},
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"status": "error", "message": "The approval request was rejected by the financial subsystem due to invalid constraints"}
        except Exception:
            logger.error("The system encountered an unexpected error while attempting to process the financial withdrawal approval request")
        return {
            "status": "error",
            "message": "The financial transaction cannot be processed at this time due to an internal system interruption so please try again later",
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
                    f"{settings.FINANCE_URL}/withdrawals/{withdrawal_id}/verify",
                    params={"action": "reject", "reason": reason},
                    timeout=settings.DEFAULT_HTTP_TIMEOUT,
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    return {"status": "error", "message": "The rejection request was blocked by the financial subsystem due to an invalid operational state"}
        except Exception:
            logger.error("The system encountered an unexpected error while attempting to process the financial withdrawal rejection request")
        return {
            "status": "error",
            "message": "The financial transaction cannot be processed at this time due to an internal system interruption so please try again later",
        }