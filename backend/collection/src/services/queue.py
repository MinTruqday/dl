import asyncio
from datetime import datetime, timezone

from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.core.infrastructure.mq import mq
from src.core.logic_logger import log_logic_execution
from src.sources.anna import AnnaSource
from src.sources.ctan import CtanSource
from src.sources.nxbgd import NxbgdSource
from src.sources.nxbst import NxbstSource


WORKER_TASKS = []
WORKER_MANAGER_TASK = None


def parse_pages(value, default=1):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(1, min(parsed, 100))


async def update_job(job_id: str | None, status: str, progress: int, error: str | None = None):
    if not job_id:
        return
    update = {
        "status": status,
        "progress": progress,
        "updated_at": datetime.now(timezone.utc),
    }
    if error:
        update["error"] = error[:500]
    if status in {"completed", "failed", "stopped"}:
        update["finished_at"] = datetime.now(timezone.utc)
    await database.mongodb[settings.COLLECTION_DB_NAME].collection_jobs.update_one(
        {"_id": job_id},
        {"$set": update},
    )


@log_logic_execution
async def run_worker():
    logger.info("Starting background message consumers")

    async def route_anna_collector(payload):
        await AnnaSource.run_list_collector(search_query="", pages=parse_pages(payload.get("pages")))

    async def route_ctan_collector(payload):
        letter = str(payload.get("pages", "a")).lower()
        await CtanSource.run_list_collector(letter)

    async def route_list_collector(payload):
        source = payload.get("source", "AnnaArchive")
        pages = parse_pages(payload.get("pages"))
        if source == "NXBST":
            await NxbstSource.run_list_collector(pages)
        elif source == "CTAN":
            await CtanSource.run_list_collector(str(payload.get("pages", "a")).lower())
        else:
            await AnnaSource.run_list_collector(search_query="", pages=pages)

    async def route_detail_collector(payload):
        url = payload.get("url")
        if not isinstance(url, str) or not url.startswith(("http://", "https://")):
            raise ValueError("Invalid detail collection URL")
        source = payload.get("source", "AnnaArchive")
        if source == "NXBST":
            await NxbstSource.run_detail_collector(url)
        elif source == "CTAN":
            await CtanSource.run_detail_collector(url)
        else:
            await AnnaSource.run_detail_collector(url)

    async def route_download_processor(payload):
        source = payload.get("source", "AnnaArchive")
        if source == "CTAN":
            await CtanSource.run_download_processor(payload)
        else:
            await AnnaSource.run_download_processor(payload)

    async def route_nxbst_collector(payload):
        url = payload.get("url")
        if url:
            await NxbstSource.run_detail_collector(url)
        else:
            await NxbstSource.run_list_collector(parse_pages(payload.get("pages")))

    async def route_nxbgd_collector(payload):
        target_class = str(payload.get("target_class", payload.get("pages", "-1")))
        await NxbgdSource(target_class).execute()

    async def poll_queue(queue_name, handler_func):
        while True:
            delivery_tag = None
            payload = None
            try:
                result = await mq.consume(queue_name, timeout=30)
                if not result:
                    continue
                if "payload" in result and "delivery_tag" in result:
                    payload = result["payload"]
                    delivery_tag = result["delivery_tag"]
                else:
                    payload = result
                job_id = payload.get("job_id") if isinstance(payload, dict) else None
                await update_job(job_id, "running", 10)
                await handler_func(payload)
                if delivery_tag:
                    await mq.ack(delivery_tag)
                await update_job(job_id, "completed", 100)
            except asyncio.CancelledError:
                if delivery_tag:
                    await mq.nack(delivery_tag, requeue=False)
                raise
            except Exception as error:
                job_id = payload.get("job_id") if isinstance(payload, dict) else None
                if delivery_tag:
                    await mq.nack(delivery_tag, requeue=False)
                await update_job(job_id, "failed", 100, str(error))
                logger.exception(f"Failed to process queue {queue_name}")
                await asyncio.sleep(1)

    queues = {
        "anna_archive_queue": route_anna_collector,
        "ctan_queue": route_ctan_collector,
        "collect_list_queue": route_list_collector,
        "collect_detail_queue": route_detail_collector,
        "download_processor_queue": route_download_processor,
        "nxbgd_queue": route_nxbgd_collector,
        "nxbst_queue": route_nxbst_collector,
    }

    global WORKER_TASKS
    WORKER_TASKS = [
        asyncio.create_task(poll_queue(name, handler), name=f"collection:{name}")
        for name, handler in queues.items()
    ]
    try:
        await asyncio.gather(*WORKER_TASKS)
    except asyncio.CancelledError:
        for task in WORKER_TASKS:
            task.cancel()
        await asyncio.gather(*WORKER_TASKS, return_exceptions=True)
        raise


async def restart_workers():
    await stop_workers()
    await start_workers()


async def start_workers():
    global WORKER_MANAGER_TASK
    if WORKER_MANAGER_TASK and not WORKER_MANAGER_TASK.done():
        return
    WORKER_MANAGER_TASK = asyncio.create_task(
        run_worker(),
        name="collection:worker-manager",
    )
    await asyncio.sleep(0)


async def stop_workers():
    global WORKER_MANAGER_TASK, WORKER_TASKS
    if WORKER_MANAGER_TASK and not WORKER_MANAGER_TASK.done():
        WORKER_MANAGER_TASK.cancel()
        await asyncio.gather(WORKER_MANAGER_TASK, return_exceptions=True)
    for task in WORKER_TASKS:
        if not task.done():
            task.cancel()
    if WORKER_TASKS:
        await asyncio.gather(*WORKER_TASKS, return_exceptions=True)
    WORKER_TASKS = []
    WORKER_MANAGER_TASK = None
