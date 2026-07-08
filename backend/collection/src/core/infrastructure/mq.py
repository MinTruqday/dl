import asyncio
import json
import uuid
import aio_pika
from loguru import logger
from typing import Any, Dict, Optional
from src.core.infrastructure.configuration import settings

class RabbitMQClient:
    def __init__(self):
        self.url = settings.RABBITMQ_URI
        self.connection = None
        self.channel = None
        self.pending_acks = {}

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
                logger.exception("Lỗi kết nối RabbitMQ, đang thử lại")
                if attempt == max_retries - 1:
                    raise e
                await asyncio.sleep(3)

    async def get_queue(self, queue_name: str):
        if not self.channel:
            await self.connect()
        
        dlx = await self.channel.declare_exchange("dlx", aio_pika.ExchangeType.DIRECT)
        dlq = await self.channel.declare_queue("dlq", durable=True)
        await dlq.bind(dlx, "dlq")
        queue_args = {
            "x-dead-letter-exchange": "dlx",
            "x-dead-letter-routing-key": "dlq",
        }
        return await self.channel.declare_queue(queue_name, durable=True, arguments=queue_args)

    async def publish(self, queue_name: str, payload: dict) -> bool:
        if not self.channel:
            await self.connect()
        try:
            message = aio_pika.Message(
                body=json.dumps(payload).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await self.channel.default_exchange.publish(message, routing_key=queue_name)
            return True
        except Exception as e:
            logger.exception("Lỗi phân phối tin nhắn vào RabbitMQ")
            return False

    async def purge(self, queue_name: str) -> bool:
        if not self.channel:
            await self.connect()
        try:
            queue = await self.get_queue(queue_name)
            await queue.purge()
            return True
        except Exception as e:
            logger.exception("Lỗi xóa hàng đợi RabbitMQ")
            return False

    async def consume(self, queue_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        if not self.channel:
            await self.connect()
        queue = await self.get_queue(queue_name)
        try:
            message = await queue.get(timeout=timeout)
            if message:
                payload = json.loads(message.body.decode())
                ack_id = str(uuid.uuid4())
                
                self.pending_acks[ack_id] = message
                
                asyncio.create_task(self._auto_nack_if_timeout(ack_id, delay=300))
                
                return {
                    "payload": payload,
                    "delivery_tag": ack_id
                }
            return None
        except aio_pika.exceptions.QueueEmpty:
            return None
        except Exception as e:
            logger.exception("Lỗi lấy tin nhắn từ RabbitMQ")
            return None

    async def _auto_nack_if_timeout(self, ack_id: str, delay: int):
        await asyncio.sleep(delay)
        message = self.pending_acks.pop(ack_id, None)
        if message:
            logger.warning(f"Quá thời gian chờ xác nhận (ACK/NACK) cho tin nhắn {ack_id} từ RabbitMQ, tiến hành thử lại")
            try:
                await message.nack(requeue=True)
            except Exception as e:
                pass

    async def ack(self, delivery_tag: str) -> bool:
        message = self.pending_acks.pop(delivery_tag, None)
        if message:
            try:
                await message.ack()
                return True
            except Exception as e:
                logger.exception("Lỗi phản hồi xác nhận (ACK) tin nhắn tới RabbitMQ")
                return False
        return False

    async def health_check(self) -> bool:
        try:
            await self.connect()
            return True
        except Exception:
            return False

    async def aclose(self):
        if self.connection:
            await self.connection.close()

mq = RabbitMQClient()
