import asyncio
from loguru import logger
from src.core.infrastructure.mq import mq
from src.sources.anna import AnnaSource
from src.sources.ctan import CtanSource
from src.sources.nxbgd import NxbgdSource
from src.sources.nxbst import NxbstSource

async def run_worker():
    logger.info("Khởi động nền tiêu thụ tin nhắn từ Queue Service")

    async def route_anna_collector(payload):
        pages = int(payload.get("pages", 0))
        await AnnaSource.run_list_collector(search_query="", pages=pages)

    async def route_ctan_collector(payload):
        pages = int(payload.get("pages", 0))
        await CtanSource.run_list_collector(pages)

    async def route_list_collector(payload):
        source = payload.get("source", "AnnaArchive")
        pages = int(payload.get("pages", 0))
        if source == "NXBST":
            await NxbstSource.run_list_collector(pages)
        elif source == "CTAN":
            await CtanSource.run_list_collector(pages)
        else:
            await AnnaSource.run_list_collector(search_query="", pages=pages)

    async def route_detail_collector(payload):
        source = payload.get("source", "AnnaArchive")
        if source == "NXBST":
            await NxbstSource.run_detail_collector(payload["url"])
        elif source == "CTAN":
            await CtanSource.run_detail_collector(payload["url"])
        else:
            await AnnaSource.run_detail_collector(payload["url"])

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
            await NxbstSource.run_list_collector(int(payload.get("pages", 0)))

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
                logger.error(f"Lỗi tiêu thụ tin nhắn từ {queue_name}: {e}")
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

    tasks = []
    for q_name, handler in queues.items():
        tasks.append(asyncio.create_task(poll_queue(q_name, handler)))

    await asyncio.gather(*tasks)
