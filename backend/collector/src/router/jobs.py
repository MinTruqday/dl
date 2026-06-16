import os
from datetime import datetime, timezone
from core.config import settings
from core.repositories.base import RepositoryFactory
from fastapi import APIRouter, HTTPException
from loguru import logger
from motor.motor_asyncio import AsyncIOMotorClient
from src.core.mq import mq_client
from uuid6 import uuid7

router = APIRouter()

@router.post("/kich-hoat")
async def trigger_collection(req: CollectionRequest):
    source = req.source
    pages = req.pages
    payload = {
        "source": source,
        "job_id": str(uuid7()),
        "triggered_at": datetime.now(timezone.utc).isoformat(),
    }
    queue_name = ""
    
    if source == "AnnaArchive":
        queue_name = "anna_archive_queue"
        payload["pages"] = pages
    elif source == "NXBST":
        queue_name = "nxbst_queue"
        payload["pages"] = pages
    elif source == "NXBGD":
        queue_name = "nxbgd_queue"
        payload["pages"] = pages
    elif source == "CTAN":
        queue_name = "ctan_queue"
        payload["pages"] = pages
    else:
        raise HTTPException(
            status_code=400, 
            detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
        )

    try:
        await mq_client.publish(queue_name, payload)
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {
            "status": "success",
            "job_id": payload["job_id"],
            "message": "Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công",
        }
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        raise HTTPException(
            status_code=500, 
            detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
        )

@router.post("/tam-dung")
async def stop_collection():
    try:
        if mq_client.channel:
            await mq_client.channel.close()
        logger.info("Yêu cầu của bạn đã được hệ thống tiếp nhận và xử lý thành công")
        return {
            "status": "success",
            "message": "Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn",
        }
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        raise HTTPException(
            status_code=500, 
            detail="Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn"
        )

@router.get("/hoat-dong-cong-viec")
async def get_active_jobs():
    active_collectors = (
        await RepositoryFactory.get("collection_jobs")
        .find({"status": {"$in": ["running", "pending"]}})
        .to_list(50)
    )
    jobs = [
        {"id": str(j["_id"]), "progress": j.get("progress", 0), "status": j["status"]}
        for j in active_collectors
    ]
    return jobs

@router.get("/thong-ke")
async def get_collector_stats():
    total_docs = await RepositoryFactory.get("documents").count_documents({})
    total_assets = await RepositoryFactory.get("archives").count_documents({})
    recent_crawls = (
        await RepositoryFactory.get("documents")
        .find({}, {"created_at": 1})
        .sort("created_at", -1)
        .limit(1)
        .to_list(length=1)
    )
    last_crawl = (
        recent_crawls[0]["created_at"].isoformat()
        if recent_crawls and isinstance(recent_crawls[0].get("created_at"), datetime)
        else None
    )
    total_collected = await RepositoryFactory.get("documents").count_documents(
        {"creator_id": {"$regex": ".*collector.*"}}
    )
    return {
        "total_documents": total_docs,
        "total_assets": total_assets,
        "collector_status": "RUNNING",
        "last_crawl": last_crawl,
        "storage_usage_mb": round(total_docs * 0.1, 2),
        "total_documents_collected": total_collected,
        "active_sources": ["AnnaArchive", "NXBST", "NXBGD", "CTAN"],
        "status": "operational",
    }

@router.get("/nhat-ky")
async def get_collector_logs():
    log_file = "logs/backend.log"
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r") as f:
            lines = f.readlines()
            filtered_lines = []
            whitelist = [
                "pipelines.nxbgd",
                "pipelines.anna",
                "pipelines.nxbst",
                "pipelines.ctan",
                "services.collector",
                "[NXBGD",
                "[NXBST",
                "[CTAN",
                "[Anna",
                "Collector",
            ]
            for line in lines:
                if any((kw.lower() in line.lower() for kw in whitelist)):
                    filtered_lines.append(line)
            logs = filtered_lines[-50:]
    return logs