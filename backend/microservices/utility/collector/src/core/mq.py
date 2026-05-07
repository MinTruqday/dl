import aio_pika
import os
import json
from loguru import logger
class RabbitMQConnection:
    def __init__(self):
        self.url = os.environ.get("RABBITMQ_URI")
        self.connection = None
        self.channel = None
    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.url)
            self.channel = await self.connection.channel()
            await self.channel.declare_queue("collect_list_queue", durable=True)
            await self.channel.declare_queue("collect_detail_queue", durable=True)
            await self.channel.declare_queue("download_processor_queue", durable=True)
            await self.channel.declare_queue("format_converter_queue", durable=True)
            await self.channel.declare_queue("nxbgd_queue", durable=True)
logger.info("Log message sanitized"))
        except Exception as e:
logger.info("Log message sanitized"))
            raise e
    async def publish(self, queue_name: str, payload: dict):
        if not self.channel:
            await self.connect()
        try:
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await self.channel.default_exchange.publish(message, routing_key=queue_name)
logger.info("Log message sanitized"))
        except Exception as e:
logger.info("Log message sanitized"))
mq_client = RabbitMQConnection()
