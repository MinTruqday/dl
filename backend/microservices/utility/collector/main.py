import asyncio
import json
from loguru import logger
from src.core.mq import mq_client
from src.pipelines.anna_archive_collector import AnnaArchiveCollector
from src.pipelines.nxbgd_collector import NXBGDCCollector
from src.pipelines.nxbst_collector import NXBSTCollector
from src.pipelines.ctan_collector import CTANCollector
from src.pipelines.format_converter import run_format_converter
async def main():
    await mq_client.connect()
    async def process_msg(message, handler_func):
        try:
            async with message.process():
                payload = json.loads(message.body.decode())
                await handler_func(payload)
        except Exception as e:
logger.info("Log message sanitized"))
    await mq_client.channel.set_qos(prefetch_count=5)
    queue_list = await mq_client.channel.get_queue("collect_list_queue")
    queue_detail = await mq_client.channel.get_queue("collect_detail_queue")
    queue_download = await mq_client.channel.get_queue("download_processor_queue")
    queue_format = await mq_client.channel.get_queue("format_converter_queue")
    queue_nxbgd = await mq_client.channel.get_queue("nxbgd_queue")
    queue_nxbst = await mq_client.channel.get_queue("nxbst_queue")
    async def route_list_collector(payload):
        source = payload.get("source", "AnnaArchive")
        if source == "NXBST":
            await NXBSTCollector.run_list_collector()
        elif source == "CTAN":
            await CTANCollector.run_list_collector()
        else:
            await AnnaArchiveCollector.run_list_collector(payload.get("url", ""), payload.get("index_type", ""))
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
    await queue_list.consume(lambda m: process_msg(m, route_list_collector))
    await queue_detail.consume(lambda m: process_msg(m, route_detail_collector))
    await queue_download.consume(lambda m: process_msg(m, route_download_processor))
    await queue_format.consume(lambda m: process_msg(m, run_format_converter))
    await queue_nxbgd.consume(lambda m: process_msg(m, lambda p: NXBGDCCollector(p.get("target_class", "10")).execute()))
logger.info("Log message sanitized"))
    await asyncio.Future()
if __name__ == "__main__":
    asyncio.run(main())
