import asyncio
import json
import os
import re
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from loguru import logger
from pymongo import ReturnDocument

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.mq import mq as mq_client
from src.core.infrastructure.mongo import mongo
from src.core.infrastructure.redis import redis
from src.schemas.ingestion import Collection
from src.clients.content import collector_document_stats
from src.sources.nxbgd import NxbgdSource


SOURCE_QUEUES = {"NXBGD": "nxbgd_queue"}


async def trigger_collection(req: Collection, retry_of: str | None = None):
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    payload = {
        "source": req.source,
        "job_id": job_id,
        "pages": req.pages,
        "max_documents": req.max_documents,
        "force_recrawl": req.force_recrawl,
        "triggered_at": now.isoformat(),
    }
    if req.source == "NXBGD":
        payload["target_class"] = str(req.pages)
    job = {
        "_id": job_id,
        "source": req.source,
        "parameters": {
            "pages": req.pages,
            "max_documents": req.max_documents,
            "force_recrawl": req.force_recrawl,
        },
        "retry_of": retry_of,
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
        raise HTTPException(
            status_code=503, detail="Không thể khởi tạo tiến trình thu thập dữ liệu"
        )


async def stop_collection():
    try:
        await redis.set("stop_collection", "1")
        queues = ["nxbgd_queue"]
        results = await asyncio.gather(*(mq_client.purge(name) for name in queues))
        if not all(results):
            raise RuntimeError("One or more queues could not be purged")
        from src.services.queue import restart_workers

        await restart_workers()
        await database.mongodb[settings.COLLECTION_DB_NAME].collection_jobs.update_many(
            {"status": {"$in": ["pending", "discovering", "running"]}},
            {"$set": {"status": "stopped", "updated_at": datetime.now(timezone.utc)}},
        )
        logger.info("Data collection process paused")
        return {"status": "success", "message": "Đã dừng toàn bộ tiến trình thu thập dữ liệu"}
    except Exception:
        logger.exception("Failed to pause data collection streams")
        raise HTTPException(status_code=503, detail="Không thể dừng tiến trình thu thập dữ liệu")


async def cancel_collection_job(job_id: str):
    collection = database.mongodb[settings.COLLECTION_DB_NAME].collection_jobs
    job = await collection.find_one({"_id": job_id})
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy collection job")
    if job.get("status") in {"completed", "failed", "stopped"}:
        return job
    await redis.setex(f"collection:cancel:{job_id}", 3600, "1")
    await collection.update_one(
        {"_id": job_id, "status": {"$in": ["pending", "discovering", "running"]}},
        {"$set": {"status": "stopping", "updated_at": datetime.now(timezone.utc)}},
    )
    return await collection.find_one({"_id": job_id})


async def retry_collection_job(job_id: str):
    collection = database.mongodb[settings.COLLECTION_DB_NAME].collection_jobs
    job = await collection.find_one_and_update(
        {"_id": job_id, "status": {"$in": ["failed", "stopped"]}},
        {"$set": {"status": "retrying", "updated_at": datetime.now(timezone.utc)}},
        return_document=ReturnDocument.BEFORE,
    )
    if not job:
        current = await collection.find_one({"_id": job_id})
        if not current:
            raise HTTPException(status_code=404, detail="Không tìm thấy collection job")
        if current.get("retry_job_id"):
            return {
                "status": "success",
                "job_id": current["retry_job_id"],
                "message": "Đã đưa tiến trình thu thập dữ liệu vào hàng đợi",
            }
        raise HTTPException(status_code=409, detail="Chỉ retry job đã thất bại hoặc đã dừng")
    parameters = job.get("parameters", {})
    request = Collection(
        source="NXBGD",
        pages=parameters.get("pages", 12),
        max_documents=parameters.get("max_documents", 1),
        force_recrawl=parameters.get("force_recrawl", False),
    )
    try:
        result = await trigger_collection(request, retry_of=job_id)
    except Exception:
        await collection.update_one(
            {"_id": job_id, "status": "retrying"},
            {"$set": {"status": job["status"], "updated_at": datetime.now(timezone.utc)}},
        )
        raise
    await collection.update_one(
        {"_id": job_id, "status": "retrying"},
        {
            "$set": {
                "status": "retried",
                "retry_job_id": result["job_id"],
                "updated_at": datetime.now(timezone.utc),
            }
        },
    )
    return result


async def get_collection_jobs(status: str | None = None):
    query = {"status": status} if status else {}
    return (
        await database.mongodb[settings.COLLECTION_DB_NAME]
        .collection_jobs.find(query)
        .sort("created_at", -1)
        .limit(500)
        .to_list(500)
    )


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
            "skipped_items": job.get("skipped_items", 0),
            "duplicate_pages": job.get("duplicate_pages", 0),
            "suspicious_pages": job.get("suspicious_pages", 0),
            "created_at": job.get("created_at"),
        }
        for job in jobs
    ]


async def get_collector_stats():
    collection = database.mongodb[settings.COLLECTION_DB_NAME].collection_jobs
    source_ids = ["nxbgd"]
    source_names = ["NXBGD"]
    content_stats = await collector_document_stats(source_ids, source_names)
    active = await collection.count_documents(
        {"status": {"$in": ["pending", "discovering", "running"]}}
    )
    failed = await collection.count_documents({"status": "failed"})
    totals = await collection.aggregate(
        [
            {
                "$group": {
                    "_id": None,
                    "duplicates_skipped": {"$sum": {"$ifNull": ["$skipped_items", 0]}},
                    "suspicious_pages": {"$sum": {"$ifNull": ["$suspicious_pages", 0]}},
                }
            }
        ]
    ).to_list(1)
    paused = await redis.get("stop_collection") == "1"
    probes = {"NXBGD": NxbgdSource.probe_list_source}

    async def source_health(source: str, probe):
        cache_key = f"collector:health:{source.lower()}"
        cached = await redis.get(cache_key)
        if cached:
            return json.loads(cached)
        result = await probe()
        result["checked_at"] = datetime.now(timezone.utc).isoformat()
        await redis.setex(cache_key, 300, json.dumps(result))
        return result

    health_rows = await asyncio.gather(
        *(source_health(source, probe) for source, probe in probes.items())
    )
    active_sources = [
        source for source, health in zip(probes, health_rows) if health.get("reachable")
    ]
    operational = not paused and len(active_sources) == len(probes)
    return {
        "total_documents": content_stats["total_documents"],
        "total_assets": content_stats["total_assets"],
        "collector_status": "PAUSED" if paused else "RUNNING" if operational else "DEGRADED",
        "last_crawl": content_stats.get("last_run"),
        "total_documents_collected": content_stats["total_collected"],
        "active_jobs": active,
        "failed_jobs": failed,
        "duplicates_skipped": totals[0]["duplicates_skipped"] if totals else 0,
        "suspicious_pages": totals[0]["suspicious_pages"] if totals else 0,
        "active_sources": active_sources,
        "source_health": health_rows,
        "status": "paused" if paused else "operational" if operational else "degraded",
    }


async def get_collector_logs():
    log_file = "logs/backend.log"
    if not os.path.isfile(log_file):
        return []
    whitelist = ["nxbgd", "collection", "rabbitmq"]
    with open(log_file, "rb") as stream:
        stream.seek(0, os.SEEK_END)
        size = stream.tell()
        stream.seek(max(0, size - 256 * 1024))
        text = stream.read().decode("utf-8", errors="ignore")
    entries = {}
    pattern = re.compile(
        r"^(\d{4}-\d{2}-\d{2}[^|]*)\|\s*(TRACE|DEBUG|INFO|WARNING|ERROR|CRITICAL)\s*\|\s*(.+)$"
    )
    for line in text.splitlines():
        match = pattern.match(line.strip())
        if not match:
            continue
        message = match.group(3).strip()
        if not any(keyword in message.lower() for keyword in whitelist):
            continue
        key = (match.group(2), message)
        current = entries.get(key, {"count": 0})
        entries[key] = {
            "timestamp": match.group(1).strip(),
            "level": match.group(2),
            "message": message,
            "count": current["count"] + 1,
        }
    rows = list(entries.values())[-50:]
    return [
        f"{row['timestamp']} · {row['level']} · {row['message']}"
        + (f" ({row['count']} lần)" if row["count"] > 1 else "")
        for row in rows
    ]
