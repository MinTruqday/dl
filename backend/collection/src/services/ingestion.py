import asyncio
import json
import os
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger
from uuid6 import uuid7

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.mq import mq as mq_client
from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.redis import redis
from src.core.logic_logger import log_logic_execution
from src.schemas.ingestion import Collection
from src.services.content_client import collector_document_stats
from src.sources.anna import AnnaSource


SOURCE_QUEUES = {
    "AnnaArchive": "anna_archive_queue",
    "NXBST": "nxbst_queue",
    "NXBGD": "nxbgd_queue",
    "CTAN": "ctan_queue",
}


@log_logic_execution
async def trigger_collection(req: Collection):
    job_id = str(uuid7())
    now = datetime.now(timezone.utc)
    payload = {
        "source": req.source,
        "job_id": job_id,
        "pages": req.pages,
        "triggered_at": now.isoformat(),
    }
    if req.source == "NXBGD":
        payload["target_class"] = str(req.pages)
    job = {
        "_id": job_id,
        "source": req.source,
        "parameters": {"pages": req.pages},
        "status": "pending",
        "progress": 0,
        "completed_items": 0,
        "failed_items": 0,
        "discovery_complete": False,
        "created_at": now,
        "updated_at": now,
    }
    db = database.mongodb[settings.COLLECTION_DB_NAME]
    await db.collection_jobs.insert_one(job)
    try:
        await redis.delete("stop_collection")
        published = await mq_client.publish(SOURCE_QUEUES[req.source], payload)
        if not published:
            raise RuntimeError("RabbitMQ rejected the collection job")
        logger.info("Background data collection initialized")
        return {
            "status": "success",
            "job_id": job_id,
            "message": "Đã đưa tiến trình thu thập dữ liệu vào hàng đợi",
        }
    except Exception:
        await db.collection_jobs.update_one(
            {"_id": job_id},
            {
                "$set": {
                    "status": "failed",
                    "error": "Không thể đưa tiến trình vào hàng đợi",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.exception("Failed to activate background data collection process")
        raise HTTPException(status_code=503, detail="Không thể khởi tạo tiến trình thu thập dữ liệu")


@log_logic_execution
async def stop_collection():
    try:
        await redis.set("stop_collection", "1")
        queues = [
            "anna_archive_queue",
            "nxbst_queue",
            "nxbgd_queue",
            "ctan_queue",
            "collect_list_queue",
            "collect_detail_queue",
            "download_processor_queue",
        ]
        results = await asyncio.gather(*(mq_client.purge(name) for name in queues))
        if not all(results):
            raise RuntimeError("One or more queues could not be purged")
        from src.services.queue import restart_workers

        await restart_workers()
        await database.mongodb[settings.COLLECTION_DB_NAME].collection_jobs.update_many(
            {"status": {"$in": ["pending", "discovering", "running"]}},
            {
                "$set": {
                    "status": "stopped",
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        logger.info("Data collection process paused")
        return {"status": "success", "message": "Đã dừng toàn bộ tiến trình thu thập dữ liệu"}
    except Exception:
        logger.exception("Failed to pause data collection streams")
        raise HTTPException(status_code=503, detail="Không thể dừng tiến trình thu thập dữ liệu")


@log_logic_execution
async def get_active_jobs():
    jobs = await mongo.find(
        "collection_jobs",
        {"status": {"$in": ["running", "discovering", "pending"]}},
        sort=[("created_at", -1)],
        limit=100,
    ).to_list(length=100)
    return [
        {
            "id": str(job["_id"]),
            "source": job.get("source"),
            "progress": job.get("progress", 0),
            "status": job["status"],
            "parameters": job.get("parameters", {}),
            "pages_scanned": job.get("pages_scanned", 0),
            "documents_detected": job.get("documents_detected", 0),
            "completed_items": job.get("completed_items", 0),
            "failed_items": job.get("failed_items", 0),
            "created_at": job.get("created_at"),
        }
        for job in jobs
    ]


@log_logic_execution
async def get_collector_stats():
    collection = database.mongodb[settings.COLLECTION_DB_NAME].collection_jobs
    source_ids = ["annas-archive", "nxbst", "nxbgd", "ctan"]
    source_names = ["Anna Archive", "NXBST", "NXBGD", "CTAN"]
    content_stats = await collector_document_stats(source_ids, source_names)
    active = await collection.count_documents(
        {"status": {"$in": ["pending", "discovering", "running"]}}
    )
    failed = await collection.count_documents({"status": "failed"})
    paused = await redis.get("stop_collection") == "1"
    cached_health = await redis.get("collector:health:anna")
    if cached_health:
        anna_health = json.loads(cached_health)
    else:
        anna_health = await AnnaSource.probe_list_source()
        anna_health["checked_at"] = datetime.now(timezone.utc).isoformat()
        await redis.setex("collector:health:anna", 300, json.dumps(anna_health))
    operational = not paused and bool(anna_health.get("reachable"))
    return {
        "total_documents": content_stats["total_documents"],
        "total_assets": content_stats["total_assets"],
        "collector_status": "PAUSED" if paused else "RUNNING" if operational else "DEGRADED",
        "last_crawl": content_stats.get("last_run"),
        "total_documents_collected": content_stats["total_collected"],
        "active_jobs": active,
        "failed_jobs": failed,
        "active_sources": ["AnnaArchive"] if anna_health.get("reachable") else [],
        "source_health": [anna_health],
        "status": "paused" if paused else "operational" if operational else "degraded",
    }


@log_logic_execution
async def get_collector_logs():
    log_file = "logs/backend.log"
    if not os.path.isfile(log_file):
        return []
    whitelist = [
        "nxbgd",
        "anna",
        "nxbst",
        "ctan",
        "collection",
        "rabbitmq",
    ]
    with open(log_file, "rb") as stream:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(max(0, size - 256 * 1024))
        text = stream.read().decode("utf-8", errors="ignore")
    return [
        line
        for line in text.splitlines()
        if any(keyword in line.lower() for keyword in whitelist)
    ][-50:]
