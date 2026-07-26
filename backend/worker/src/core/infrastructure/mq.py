import asyncio
import json
import re

import aio_pika

from src.core.infrastructure.configuration import settings


QUEUE_PATTERN = re.compile(r"^[a-z0-9_]{1,100}$")


class RabbitMQClient:
    def __init__(self):
        self.connection = None
        self.channel = None
        self._connect_lock = asyncio.Lock()
        self._topology_lock = asyncio.Lock()

    async def connect(self):
        async with self._connect_lock:
            if (
                self.connection
                and not self.connection.is_closed
                and self.channel
                and not self.channel.is_closed
            ):
                return
            if self.connection and not self.connection.is_closed:
                await self.connection.close()
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URI)
            self.channel = await self.connection.channel(publisher_confirms=True)
            await self.channel.set_qos(prefetch_count=2)

    async def get_queue(self, queue_name: str):
        if not QUEUE_PATTERN.fullmatch(queue_name):
            raise ValueError("Invalid queue name")
        async with self._topology_lock:
            await self.connect()
            dlx = await self.channel.declare_exchange(
                "dlx",
                aio_pika.ExchangeType.DIRECT,
            )
            dlq = await self.channel.declare_queue("dlq", durable=True)
            await dlq.bind(dlx, "dlq")
            return await self.channel.declare_queue(
                queue_name,
                durable=True,
                arguments={
                    "x-dead-letter-exchange": "dlx",
                    "x-dead-letter-routing-key": "dlq",
                },
            )

    async def publish(self, queue_name: str, payload: dict) -> bool:
        await self.get_queue(queue_name)
        message = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
            message_id=str(payload.get("job_id", "")) or None,
        )
        confirmation = await self.channel.default_exchange.publish(
            message,
            routing_key=queue_name,
            mandatory=True,
        )
        return confirmation is not False

    async def health_check(self) -> bool:
        await self.connect()
        return bool(self.connection and not self.connection.is_closed)

    async def aclose(self):
        if self.channel and not self.channel.is_closed:
            await self.channel.close()
        if self.connection and not self.connection.is_closed:
            await self.connection.close()
        self.channel = None
        self.connection = None


mq = RabbitMQClient()
