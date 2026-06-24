import asyncio
import json
import aio_pika
from loguru import logger
from src.core.infrastructure.configuration import settings

class RabbitMQCore:
    def __init__(self):
        self.url = settings.RABBITMQ_URI
        self.connection = None
        self.channel = None

    async def connect(self):
        if self.connection and not self.connection.is_closed:
            return

        max_retries = 10
        for attempt in range(max_retries):
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                logger.info("Kết nối RabbitMQ thành công")
                return
            except Exception as e:
                logger.error(f"Lỗi kết nối RabbitMQ, đang thử lại: {e}")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(3)

    async def get_queue(self, queue_name: str):
        if not self.channel:
            await self.connect()
        # Declare dead-letter exchange
        dlx = await self.channel.declare_exchange("dlx", aio_pika.ExchangeType.DIRECT)
        dlq = await self.channel.declare_queue("dlq", durable=True)
        await dlq.bind(dlx, "dlq")
        queue_args = {
            "x-dead-letter-exchange": "dlx",
            "x-dead-letter-routing-key": "dlq",
        }
        return await self.channel.declare_queue(queue_name, durable=True, arguments=queue_args)

    async def publish(self, queue_name: str, payload: dict):
        if not self.channel:
            await self.connect()
        try:
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await self.channel.default_exchange.publish(message, routing_key=queue_name)
            logger.debug(f"Đã gửi tin nhắn đến {queue_name}")
            return True
        except Exception as e:
            logger.error(f"Lỗi phân phối tin nhắn: {e}")
            return False

    async def consume(self, queue_name: str, timeout: int = 30):
        if not self.channel:
            await self.connect()
        queue = await self.get_queue(queue_name)
        try:
            message = await queue.get(timeout=timeout)
            if message:
                payload = json.loads(message.body.decode())
                # Return the payload. The caller must ACK later, but for simplicity of HTTP we can auto-ack or require manual ack.
                # Actually, HTTP Long-Polling with manual ACK is hard because the consumer might die.
                # So we will just auto_ack on HTTP return to keep it simple, or push to Webhook.
                # Since we are wrapping RabbitMQ, we will just auto_ack upon successful GET.
                await message.ack()
                return payload
            return None
        except aio_pika.exceptions.QueueEmpty:
            return None
        except Exception as e:
            logger.error(f"Lỗi lấy tin nhắn: {e}")
            return None

    async def close(self):
        if self.connection:
            await self.connection.close()

rabbitmq = RabbitMQCore()
