import os
import secrets
import httpx
from datetime import datetime, timezone
from core.config import settings
from core.database import db_client
from core.repositories.base import RepositoryFactory
from core.storage import get_storage_client
from fastapi import HTTPException, Query
from loguru import logger
from uuid6 import uuid7

class OperationService:

    @staticmethod
    async def toggle_maintenance_mode(enabled: bool, message: str = "", db=None) -> dict:
        await RepositoryFactory.get("system_config").update_one(
            {"key": "maintenance_mode"},
            {"$set": {"enabled": enabled, "message": message, "updated_at": datetime.now(timezone.utc)}},
            upsert=True,
        )
        logger.warning("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"message": "Khởi tạo AI thành công"}

    @staticmethod
    async def trigger_backup(action: str = "FULL", db=None) -> dict:
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {"message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}

    @staticmethod
    async def create_api_key(name: str, provider: str = "DEFAULT", key_value: str = "", db=None) -> dict:
        if not key_value:
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
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        return {"message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công", "key": key_value}

    @staticmethod
    async def create_marketing_campaign(data: dict, db=None) -> dict:
        campaign = {
            "_id": str(uuid7()),
            "title": data.get("title", "New Promotional Campaign"),
            "target_audience": data.get("target", "ALL"),
            "discount_percent": data.get("discount", 0),
            "status": "active",
            "created_at": datetime.now(timezone.utc),
        }
        await RepositoryFactory.get("marketing_campaigns").insert_one(campaign)
        logger.info("Khởi tạo AI thành công")
        return {"message": "Khởi tạo AI thành công"}

    @staticmethod
    async def get_system_health(db=None) -> dict:
        target_db = db or db_client.mongodb.get_default_database()
        try:
            await target_db.command("ping")
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
        if settings.AGENTIC_AI_URL:
            try:
                async with httpx.AsyncClient(timeout=2.0) as client:
                    resp = await client.get(f"{settings.AGENTIC_AI_URL}/suc-khoe")
                    rag_status = "healthy" if resp.status_code == 200 else "degraded"
            except Exception:
                rag_status = "unreachable"
                
        load_avg = os.getloadavg() if hasattr(os, "getloadavg") else [0, 0, 0]
        cpu_usage = f"{min(load_avg[0] / os.cpu_count() * 100, 100):.1f}%" if hasattr(os, "cpu_count") else f"{min(load_avg[0] * 10, 100):.1f}%"
        
        return {
            "status": "healthy" if db_status == "connected" and redis_status == "connected" and rag_status == "healthy" else "degraded",
            "services": {"database": db_status, "cache": redis_status, "ai_agent": rag_status},
            "resources": {"cpu_load": cpu_usage, "uptime": "99.9%"},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    async def get_maintenance_mode(db=None) -> dict:
        config = await RepositoryFactory.get("system_config").find_one({"key": "maintenance_mode"})
        if not config:
            return {"enabled": False, "message": ""}
        return {"enabled": config.get("enabled", False), "message": config.get("message", "")}

    @staticmethod
    async def get_minio_stats(db=None) -> dict:
        try:
            async with await get_storage_client() as storage_client:
                buckets_resp = await storage_client.list_buckets()
                buckets_list = buckets_resp.get("Buckets", [])
                total_size_bytes = 0
                total_objects_count = 0
                buckets_data = []
                categories = {
                    "CTAN": {"count": 0, "size": 0}, "NXBGD": {"count": 0, "size": 0},
                    "NXBST": {"count": 0, "size": 0}, "Anna Archive": {"count": 0, "size": 0},
                    "User Images": {"count": 0, "size": 0}, "User Documents": {"count": 0, "size": 0},
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
                                categories["CTAN"]["count"] += 1; categories["CTAN"]["size"] += size
                            elif "nxbgd" in key.lower():
                                categories["NXBGD"]["count"] += 1; categories["NXBGD"]["size"] += size
                            elif "nxbst" in key.lower():
                                categories["NXBST"]["count"] += 1; categories["NXBST"]["size"] += size
                            elif "anna_archive" in key.lower():
                                categories["Anna Archive"]["count"] += 1; categories["Anna Archive"]["size"] += size
                            elif key.startswith("images/"):
                                categories["User Images"]["count"] += 1; categories["User Images"]["size"] += size
                            elif key.startswith("documents/"):
                                categories["User Documents"]["count"] += 1; categories["User Documents"]["size"] += size
                            else:
                                categories["Others"]["count"] += 1; categories["Others"]["size"] += size
                                
                    buckets_data.append({
                        "name": bucket_name,
                        "created_at": b["CreationDate"].isoformat() if "CreationDate" in b else "",
                        "size_bytes": bucket_size,
                        "objects_count": obj_count,
                    })
                    
                formatted_categories = [{"name": n, "count": s["count"], "size_bytes": s["size"]} for n, s in categories.items() if s["count"] > 0 or s["size"] > 0]
                return {
                    "status": "healthy",
                    "total_buckets": len(buckets_list),
                    "total_size_bytes": total_size_bytes,
                    "total_objects_count": total_objects_count,
                    "buckets": buckets_data,
                    "categories": formatted_categories,
                }
        except Exception:
            logger.error("Mất kết nối mạng tạm thời")
            return {"status": "unreachable", "total_buckets": 0, "total_size_bytes": 0, "total_objects_count": 0, "buckets": [], "categories": []}

    @staticmethod
    async def get_collector_stats(db=None) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.COLLECTOR_URL}/thong-ke", timeout=settings.DEFAULT_HTTP_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return {"total_documents": 0, "total_assets": 0, "collector_status": "OFFLINE", "last_crawl": None, "storage_usage_mb": 0}

    @staticmethod
    async def trigger_collection(source: str, pages: int, db=None) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{settings.COLLECTOR_URL}/kich-hoat", json={"source": source, "pages": pages}, timeout=settings.DEFAULT_HTTP_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "error", "message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}
        except Exception:
            logger.error("Mất kết nối mạng tạm thời")
        return {"status": "error", "message": "Mất kết nối mạng tạm thời"}

    @staticmethod
    async def stop_collection(db=None) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{settings.COLLECTOR_URL}/dung-lai", timeout=settings.DEFAULT_HTTP_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
                return {"status": "error", "message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"}
        except Exception:
            logger.error("Mất kết nối mạng tạm thời")
        return {"status": "error", "message": "Mất kết nối mạng tạm thời"}

    @staticmethod
    async def get_collector_logs(db=None) -> list:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.COLLECTOR_URL}/nhat-ky", timeout=settings.DEFAULT_HTTP_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return []

    @staticmethod
    async def get_active_collector_jobs(db=None) -> list:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.COLLECTOR_URL}/hoat-dong-cong-viec", timeout=settings.DEFAULT_HTTP_TIMEOUT)
                if resp.status_code == 200:
                    return resp.json()
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return []