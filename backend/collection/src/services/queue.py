import asyncio
from src.core.logic_logger import log_logic_execution
from loguru import logger
from src.core.infrastructure.mq import mq
from src.sources.anna import AnnaSource
from src.sources.ctan import CtanSource
from src.sources.nxbgd import NxbgdSource
from src.sources.nxbst import NxbstSource

WORKER_TASKS = []

@log_logic_execution
async def run_worker():
    logger.info("Starting background message consumer for Queue service")

    @log_logic_execution
    async def route_anna_collector(payload):
        pages = int(payload.get("pages", 0))
        await AnnaSource.run_list_collector(search_query="", pages=pages)

    @log_logic_execution
    async def route_ctan_collector(payload):
        pages = payload.get("pages", 0)
        if isinstance(pages, str) and not pages.isdigit():
            pages = 0
        else:
            pages = int(pages)
        await CtanSource.run_list_collector(pages)

    @log_logic_execution
    async def route_list_collector(payload):
        source = payload.get("source", "AnnaArchive")
        raw_pages = payload.get("pages", 0)
        if isinstance(raw_pages, str) and not raw_pages.isdigit():
            pages = 0
        else:
            pages = int(raw_pages)
        if source == "NXBST":
            await NxbstSource.run_list_collector(pages)
        elif source == "CTAN":
            await CtanSource.run_list_collector(pages)
        else:
            await AnnaSource.run_list_collector(search_query="", pages=pages)

    @log_logic_execution
    async def route_detail_collector(payload):
        source = payload.get("source", "AnnaArchive")
        if source == "NXBST":
            await NxbstSource.run_detail_collector(payload["url"])
        elif source == "CTAN":
            await CtanSource.run_detail_collector(payload["url"])
        else:
            await AnnaSource.run_detail_collector(payload["url"])

    @log_logic_execution
    async def route_download_processor(payload):
        source = payload.get("source", "AnnaArchive")
        if source == "CTAN":
            await CtanSource.run_download_processor(payload)
        else:
            await AnnaSource.run_download_processor(payload)

    @log_logic_execution
    async def route_nxbst_collector(payload):
        url = payload.get("url")
        if url:
            await NxbstSource.run_detail_collector(url)
        else:
            await NxbstSource.run_list_collector(int(payload.get("pages", 0)))

    @log_logic_execution
    async def poll_queue(queue_name, handler_func):
        while True:
            try:
                res = await mq.consume(queue_name, timeout=30)
                if res and "payload" in res and "delivery_tag" in res:
                    payload = res["payload"]
                    delivery_tag = res["delivery_tag"]
                    await handler_func(payload)
                    
                    await mq.ack(delivery_tag)
                elif res: 
                    await handler_func(res)
            except Exception as e:
                logger.exception(f"Failed to consume from queue {queue_name} in RabbitMQ")
                await asyncio.sleep(5)
            await asyncio.sleep(1)

    queues = {
        "anna_archive_queue": route_anna_collector,
        "ctan_queue": route_ctan_collector,
        "collect_list_queue": route_list_collector,
        "collect_detail_queue": route_detail_collector,
        "download_processor_queue": route_download_processor,
        "nxbgd_queue": lambda p: NxbgdSource(p.get("target_class", "-1")).execute(),
        "nxbst_queue": route_nxbst_collector,
    }

    global WORKER_TASKS
    WORKER_TASKS = []
    for q_name, handler in queues.items():
        WORKER_TASKS.append(asyncio.create_task(poll_queue(q_name, handler)))

    try:
        await asyncio.gather(*WORKER_TASKS)
    except asyncio.CancelledError:
        logger.info("Worker tasks have been cancelled")

async def restart_workers():
    global WORKER_TASKS
    for t in WORKER_TASKS:
        t.cancel()
    
    await asyncio.sleep(2)
    asyncio.create_task(run_worker())
