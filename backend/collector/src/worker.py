import asyncio
import json
from loguru import logger
from src.core.mq import mq_client
from src.pipelines.anna_archive import AnnaArchivePipeline
from src.pipelines.ctan import CTANPipeline
from src.pipelines.nxbgd import NXBGDPipeline
from src.pipelines.nxbst import NXBSTPipeline

async def run_worker():
    await mq_client.connect()

    async def process_msg(message, handler_func):
        try:
            async with message.process():
                payload = json.loads(message.body.decode())
                await handler_func(payload)
        except Exception:
            logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
            raise

    await mq_client.channel.set_qos(prefetch_count=2)
    semaphore = asyncio.Semaphore(2)

    async def process_msg_with_sem(message, handler_func):
        async with semaphore:
            await process_msg(message, handler_func)

    queue_list = await mq_client.channel.get_queue("collect_list_queue")
    queue_detail = await mq_client.channel.get_queue("collect_detail_queue")
    queue_download = await mq_client.channel.get_queue("download_processor_queue")
    queue_nxbgd = await mq_client.channel.get_queue("nxbgd_queue")
    queue_nxbst = await mq_client.channel.get_queue("nxbst_queue")
    queue_anna = await mq_client.channel.get_queue("anna_archive_queue")
    queue_ctan = await mq_client.channel.get_queue("ctan_queue")

    async def route_anna_collector(payload):
        pages = int(payload.get("pages", 0))
        await AnnaArchivePipeline.collect_list(search_query="", pages=pages)

    async def route_ctan_collector(payload):
        pages = int(payload.get("pages", 0))
        await CTANPipeline.collect_list(pages)

    async def route_list_collector(payload):
        source = payload.get("source", "AnnaArchive")
        pages = int(payload.get("pages", 0))
        if source == "NXBST":
            await NXBSTPipeline.collect_list(pages)
        elif source == "CTAN":
            await CTANPipeline.collect_list(pages)
        else:
            await AnnaArchivePipeline.collect_list(search_query="", pages=pages)

    async def route_detail_collector(payload):
        source = payload.get("source", "AnnaArchive")
        if source == "NXBST":
            await NXBSTPipeline.collect_detail(payload["url"])
        elif source == "CTAN":
            await CTANPipeline.collect_detail(payload["url"])
        else:
            await AnnaArchivePipeline.collect_detail(payload["url"])

    async def route_download_processor(payload):
        source = payload.get("source", "AnnaArchive")
        if source == "CTAN":
            await CTANPipeline.process_download(payload)
        else:
            await AnnaArchivePipeline.process_download(payload)

    async def route_nxbst_collector(payload):
        url = payload.get("url")
        if url:
            await NXBSTPipeline.collect_detail(url)
        else:
            await NXBSTPipeline.collect_list(int(payload.get("pages", 0)))

    await queue_anna.consume(lambda m: process_msg_with_sem(m, route_anna_collector))
    await queue_ctan.consume(lambda m: process_msg_with_sem(m, route_ctan_collector))
    await queue_list.consume(lambda m: process_msg_with_sem(m, route_list_collector))
    await queue_detail.consume(lambda m: process_msg_with_sem(m, route_detail_collector))
    await queue_download.consume(lambda m: process_msg_with_sem(m, route_download_processor))
    await queue_nxbgd.consume(lambda m: process_msg_with_sem(m, lambda p: NXBGDPipeline(p.get("target_class", "-1")).execute()))
    await queue_nxbst.consume(lambda m: process_msg_with_sem(m, route_nxbst_collector))

    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Hệ thống đang tiến hành xử lý dữ liệu theo yêu cầu của bạn")
        stop_event.set()

    await stop_event.wait()
    logger.info("Mất kết nối mạng tạm thời")
    await mq_client.connection.close()