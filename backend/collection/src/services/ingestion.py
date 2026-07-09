from src.core.logic_logger import log_logic_execution
from src.core.infrastructure.mongo import mongo
import os
import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from loguru import logger

from src.core.infrastructure.mq import mq as mq_client
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.schemas.ingestion import Collection
from src.repositories.archive import ArchiveRepository

from src.core.infrastructure.redis import redis

@log_logic_execution
async def trigger_collection(req: Collection):
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
            status_code=400, detail="Nguồn dữ liệu không được hệ thống hỗ trợ"
        )

    try:
        await redis.delete("stop_collection")
        await mq_client.publish(queue_name, payload)
        logger.info("Background data collection initialized successfully")
        return {
            "status": "success",
            "job_id": payload["job_id"],
            "message": "Đang bắt đầu tiến trình thu thập dữ liệu ngầm",
        }
    except Exception as e:
        logger.exception("Failed to activate background data collection process")
        raise HTTPException(
            status_code=500, detail=f"Không thể đưa tiến trình thu thập dữ liệu vào hàng đợi {e}"
        )

@log_logic_execution
async def stop_collection():
    try:
        await redis.set("stop_collection", "1")
        queues = [
            "anna_archive_queue", "nxbst_queue", "nxbgd_queue", "ctan_queue",
            "collect_list_queue", "collect_detail_queue", "download_processor_queue"
        ]
        for q in queues:
            await mq_client.purge(q)

        from src.services.queue import restart_workers
        asyncio.create_task(restart_workers())

        logger.info("Data collection process paused successfully")
        return {
            "status": "success",
            "message": "Đã tạm dừng toàn bộ tiến trình thu thập dữ liệu",
        }
    except Exception as e:
        logger.exception("Failed to transmit pause signal to data collection streams")
        raise HTTPException(
            status_code=500, detail=f"Lỗi khi gửi lệnh tạm dừng đến tiến trình nền {e}"
        )

@log_logic_execution
async def get_active_jobs():
    active_collectors = await mongo.find(
        "collection_jobs", {"status": {"$in": ["running", "pending"]}}
    )
    jobs = [
        {"id": str(j["_id"]), "progress": j.get("progress", 0), "status": j["status"]}
        for j in active_collectors
    ]
    return jobs

@log_logic_execution
async def get_collector_stats():
    total_docs = await ArchiveRepository.count_documents({})
    total_assets = await ArchiveRepository.count_documents({})
    recent_crawls = await mongo.find(
        "documents", {}, {"created_at": 1}, sort=[("created_at", -1)], limit=1
    )
    last_crawl = (
        recent_crawls[0]["created_at"].isoformat()
        if recent_crawls and len(recent_crawls) > 0 and isinstance(recent_crawls[0].get("created_at"), datetime)
        else None
    )
    total_collected = await ArchiveRepository.count_documents(
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

@log_logic_execution
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
                "[AnnaSource",
                "DataCollection",
            ]
            for line in lines:
                if any((kw.lower() in line.lower() for kw in whitelist)):
                    filtered_lines.append(line)
            logs = filtered_lines[-50:]
    return logs
