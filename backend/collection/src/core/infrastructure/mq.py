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
        self.consumer_channels = {}
        self.pending_acks = {}

    async def connect(self):
        if (
            self.connection
            and not self.connection.is_closed
            and self.channel
            and not self.channel.is_closed
        ):
            return

        max_retries = 10
        for attempt in range(max_retries):
            try:
                self.connection = await aio_pika.connect_robust(self.url)
                self.channel = await self.connection.channel()
                logger.info("RabbitMQ connection established")
                return
            except Exception:
                logger.warning("RabbitMQ connection failed, retrying")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2)

    async def get_queue(self, queue_name: str):
        if not self.channel or self.channel.is_closed:
            await self.connect()

        dlx = await self.channel.declare_exchange("dlx", aio_pika.ExchangeType.DIRECT)
        dlq = await self.channel.declare_queue("dlq", durable=True)
        await dlq.bind(dlx, "dlq")
        queue_args = {"x-dead-letter-exchange": "dlx", "x-dead-letter-routing-key": "dlq"}
        return await self.channel.declare_queue(queue_name, durable=True, arguments=queue_args)

    async def publish(self, queue_name: str, payload: dict) -> bool:
        if not self.channel or self.channel.is_closed:
            await self.connect()
        try:
            message = aio_pika.Message(
                body=json.dumps(payload).encode(), delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            await self.channel.default_exchange.publish(message, routing_key=queue_name)
            return True
        except Exception:
            logger.exception("RabbitMQ message publishing failed")
            raise

    async def purge(self, queue_name: str) -> bool:
        if not self.channel or self.channel.is_closed:
            await self.connect()
        try:
            queue = await self.get_queue(queue_name)
            await queue.purge()
            return True
        except Exception:
            logger.exception("RabbitMQ queue purge failed")
            return False

    async def consume(self, queue_name: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        if not self.connection or self.connection.is_closed:
            await self.connect()
        channel = self.consumer_channels.get(queue_name)
        if channel is None or channel.is_closed:
            channel = await self.connection.channel()
            self.consumer_channels[queue_name] = channel
        dlx = await channel.declare_exchange("dlx", aio_pika.ExchangeType.DIRECT)
        dlq = await channel.declare_queue("dlq", durable=True)
        await dlq.bind(dlx, "dlq")
        queue = await channel.declare_queue(
            queue_name,
            durable=True,
            arguments={"x-dead-letter-exchange": "dlx", "x-dead-letter-routing-key": "dlq"},
        )
        try:
            message = await queue.get(timeout=timeout)
            if message:
                try:
                    payload = json.loads(message.body.decode())
                except (UnicodeDecodeError, json.JSONDecodeError):
                    await message.reject(requeue=False)
                    logger.warning("RabbitMQ discarded a malformed message")
                    return None
                ack_id = str(uuid.uuid4())

                self.pending_acks[ack_id] = message

                asyncio.create_task(self._auto_nack_if_timeout(ack_id, delay=300))

                return {"payload": payload, "delivery_tag": ack_id}
            return None
        except aio_pika.exceptions.QueueEmpty:
            return None
        except Exception:
            logger.exception("RabbitMQ message consumption failed")
            return None

    async def _auto_nack_if_timeout(self, ack_id: str, delay: int):
        await asyncio.sleep(delay)
        message = self.pending_acks.pop(ack_id, None)
        if message:
            logger.warning(f"RabbitMQ message {ack_id} ACK/NACK timed out, attempting requeue")
            try:
                await message.nack(requeue=True)
            except Exception:
                logger.exception("RabbitMQ automatic NACK failed")

    async def ack(self, delivery_tag: str) -> bool:
        message = self.pending_acks.pop(delivery_tag, None)
        if message:
            try:
                await message.ack()
                return True
            except Exception as e:
                logger.exception("RabbitMQ ACK confirmation failed")
                return False
        return False

    async def nack(self, delivery_tag: str, requeue: bool = True) -> bool:
        message = self.pending_acks.pop(delivery_tag, None)
        if not message:
            return False
        try:
            await message.nack(requeue=requeue)
            return True
        except Exception:
            logger.exception("RabbitMQ NACK failed")
            return False

    async def health_check(self) -> bool:
        try:
            await self.connect()
            return True
        except Exception:
            return False

    async def aclose(self):
        for message in list(self.pending_acks.values()):
            if not message.processed:
                await message.nack(requeue=True)
        self.pending_acks.clear()
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        for channel in self.consumer_channels.values():
            if not channel.is_closed:
                await channel.close()
        self.consumer_channels.clear()
        if self.connection:
            await self.connection.close()
        self.channel = None
        self.connection = None


mq = RabbitMQClient()
