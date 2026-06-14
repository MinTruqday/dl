import json
import os

import aio_pika
from core.config import settings
from loguru import logger


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

                dlx = await self.channel.declare_exchange(
                    "dlx_collector", aio_pika.ExchangeType.DIRECT
                )
                dlq = await self.channel.declare_queue(
                    "dlq_collector_queue", durable=True
                )
                await dlq.bind(dlx, "dlq")

                queue_args = {
                    "x-dead-letter-exchange": "dlx_collector",
                    "x-dead-letter-routing-key": "dlq",
                }

                await self.channel.declare_queue(
                    "collect_list_queue", durable=True, arguments=queue_args
                )
                await self.channel.declare_queue(
                    "collect_detail_queue", durable=True, arguments=queue_args
                )
                await self.channel.declare_queue(
                    "download_processor_queue", durable=True, arguments=queue_args
                )
                await self.channel.declare_queue(
                    "format_converter_queue", durable=True, arguments=queue_args
                )
                await self.channel.declare_queue(
                    "nxbgd_queue", durable=True, arguments=queue_args
                )
                await self.channel.declare_queue(
                    "nxbst_queue", durable=True, arguments=queue_args
                )
                await self.channel.declare_queue(
                    "anna_archive_queue", durable=True, arguments=queue_args
                )
                await self.channel.declare_queue(
                    "ctan_queue", durable=True, arguments=queue_args
                )

                logger.info("Successfully connected to RabbitMQ broker")
                return
            except Exception as e:
                logger.error(f"RabbitMQ connection attempt {attempt + 1}/{max_retries} failed")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(3)

    async def publish(self, queue_name: str, payload: dict):
        if not self.channel:
            await self.connect()
        try:
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await self.channel.default_exchange.publish(message, routing_key=queue_name)
            logger.debug(
                f"Successfully dispatched message to {queue_name}: {payload.get('url', payload.get('title', 'ping'))}"
            )
        except Exception as e:
            logger.error(f"Message distribution failed for queue {queue_name}")


mq_client = RabbitMQConnection()
