import asyncio
import json
from loguru import logger
from src.core.mq import mq_client
from src.pipelines.anna_archive_collector import AnnaArchiveCollector
from src.pipelines.nxbgd_collector import NXBGDCollector
from src.pipelines.nxbst_collector import NXBSTCollector
from src.pipelines.ctan_collector import CTANCollector
async def run_worker():
    import sys
    logger.add(sys.stdout, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
    logger.add("logs/backend.log", format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} - {message}", rotation="10 MB", level="INFO")
    
    await mq_client.connect()
    
    async def process_msg(message, handler_func):
        try:
            async with message.process():
                payload = json.loads(message.body.decode())
                await handler_func(payload)
        except Exception as e:
            logger.error(f"Error processing message: {e}\nPayload: {message.body.decode()}")
            raise
            
    await mq_client.channel.set_qos(prefetch_count=2)
    semaphore = asyncio.Semaphore(2)

    async def process_msg_with_sem(message, handler_func):
        async with semaphore:
            await process_msg(message, handler_func)
    
    queue_list = await mq_client.channel.get_queue("collect_list_queue")
    queue_detail = await mq_client.channel.get_queue("collect_detail_queue")
    queue_download = await mq_client.channel.get_queue("download_processor_queue")
    queue_format = await mq_client.channel.get_queue("format_converter_queue")
    queue_nxbgd = await mq_client.channel.get_queue("nxbgd_queue")
    queue_nxbst = await mq_client.channel.get_queue("nxbst_queue")
    queue_anna = await mq_client.channel.get_queue("anna_archive_queue")
    queue_ctan = await mq_client.channel.get_queue("ctan_queue")

    async def route_anna_collector(payload):
        pages = int(payload.get("pages", 0))
        await AnnaArchiveCollector.run_list_collector(search_query="", pages=pages)

    async def route_ctan_collector(payload):
        pages = int(payload.get("pages", 0))
        await CTANCollector.run_list_collector(pages)

    async def route_list_collector(payload):
        source = payload.get("source", "AnnaArchive")
        pages = int(payload.get("pages", 0))
        if source == "NXBST":
            await NXBSTCollector.run_list_collector(pages)
        elif source == "CTAN":
            await CTANCollector.run_list_collector(pages)
        else:
            await AnnaArchiveCollector.run_list_collector(search_query="", pages=pages)

    async def route_detail_collector(payload):
        source = payload.get("source", "AnnaArchive")
        if source == "NXBST":
            await NXBSTCollector.run_detail_collector(payload["url"])
        elif source == "CTAN":
            await CTANCollector.run_detail_collector(payload["url"])
        else:
            await AnnaArchiveCollector.run_detail_collector(payload["url"])

    async def route_download_processor(payload):
        source = payload.get("source", "AnnaArchive")
        if source == "CTAN":
            await CTANCollector.run_download_processor(payload)
        else:
            await AnnaArchiveCollector.run_download_processor(payload)

    async def route_nxbst_collector(payload):
        url = payload.get("url")
        if url:
            await NXBSTCollector.run_detail_collector(url)
        else:
            await NXBSTCollector.run_list_collector(int(payload.get("pages", 0)))

    await queue_anna.consume(lambda m: process_msg_with_sem(m, route_anna_collector))
    await queue_ctan.consume(lambda m: process_msg_with_sem(m, route_ctan_collector))
    await queue_list.consume(lambda m: process_msg_with_sem(m, route_list_collector))
    await queue_detail.consume(lambda m: process_msg_with_sem(m, route_detail_collector))
    
    await queue_download.consume(lambda m: process_msg_with_sem(m, route_download_processor))

    await queue_nxbgd.consume(lambda m: process_msg_with_sem(m, lambda p: NXBGDCollector(p.get("target_class", "-1")).execute()))
    await queue_nxbst.consume(lambda m: process_msg_with_sem(m, route_nxbst_collector))
    
    logger.info("DocLib Collector 0.1a initialized - Listening to collector events from RabbitMQ")
    
    stop_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received, shutting down gracefully")
        stop_event.set()

    import signal
    
    # loop = asyncio.get_event_loop()
    # for sig in (signal.SIGINT, signal.SIGTERM):
    #     loop.add_signal_handler(sig, signal_handler)
        
    await stop_event.wait()
    
    logger.info("Closing MQ connection")
    await mq_client.connection.close()
    logger.info("Shutdown complete.")
