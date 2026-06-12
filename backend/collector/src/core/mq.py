import aio_pika
import os
import json
from loguru import logger

from core.config import settings

class RabbitMQConnection:
    def __init__(self):
        self.url = settings.RABBITMQ_URI
        self.connection = None
        self.channel = None

    async def connect(self):
        import asyncio
        max_retries = 10
        for attempt in range(max_retries):
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()

                dlx = await self.channel.declare_exchange('dlx_collector', aio_pika.ExchangeType.DIRECT)
                dlq = await self.channel.declare_queue('dlq_collector_queue', durable=True)
                await dlq.bind(dlx, 'dlq')
                
                queue_args = {'x-dead-letter-exchange': 'dlx_collector', 'x-dead-letter-routing-key': 'dlq'}

                await self.channel.declare_queue("collect_list_queue", durable=True, arguments=queue_args)
                await self.channel.declare_queue("collect_detail_queue", durable=True, arguments=queue_args)
                await self.channel.declare_queue("download_processor_queue", durable=True, arguments=queue_args)
                await self.channel.declare_queue("format_converter_queue", durable=True, arguments=queue_args)
                await self.channel.declare_queue("nxbgd_queue", durable=True, arguments=queue_args)
                await self.channel.declare_queue("nxbst_queue", durable=True, arguments=queue_args)
                await self.channel.declare_queue("anna_archive_queue", durable=True, arguments=queue_args)
                await self.channel.declare_queue("ctan_queue", durable=True, arguments=queue_args)
                
                logger.info('Kết nối RabbitMQ thành công')
                return
            except Exception as e:
                logger.error(f'Lỗi kết nối RabbitMQ lần {attempt + 1}/{max_retries}')
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(3)

    async def publish(self, queue_name: str, payload: dict):
        if not self.channel:
            await self.connect()
        try:
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await self.channel.default_exchange.publish(message, routing_key=queue_name)
            logger.debug(f"Điều phối tới {queue_name} {payload.get('url', payload.get('title', 'ping'))} thành công")
        except Exception as e:
            logger.error(f'Lỗi phân phối sự kiện tới {queue_name}')

mq_client = RabbitMQConnection()
