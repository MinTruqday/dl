import asyncio
import json
from typing import Any, Callable, Dict

import aio_pika
from loguru import logger

from src.core.infrastructure.configuration import settings

class EventBus:
    def __init__(self):
        self.connection: aio_pika.RobustConnection | None = None
        self.channel: aio_pika.Channel | None = None
        self.exchange: aio_pika.Exchange | None = None

    async def connect(self):
        if not settings.RABBITMQ_URI:
            logger.warning("RABBITMQ_URI is not set. EventBus will not connect")
            return

        try:
            self.connection = await aio_pika.connect_robust(settings.RABBITMQ_URI)
            self.channel = await self.connection.channel()
            self.exchange = await self.channel.declare_exchange(
                "agentic_events", aio_pika.ExchangeType.TOPIC
            )
            logger.info("Connected to RabbitMQ Event Bus")
        except Exception as e:
            logger.error("Failed to connect to RabbitMQ")

    async def publish(self, routing_key: str, message: Dict[str, Any]):
        if not self.exchange:
            return
        
        try:
            msg_body = json.dumps(message).encode()
            await self.exchange.publish(
                aio_pika.Message(body=msg_body),
                routing_key=routing_key,
            )
            logger.debug(f"Published event [{routing_key}]: {message}")
        except Exception as e:
            logger.error(f"Error publishing event {routing_key}")

    async def subscribe(self, routing_key: str, callback: Callable[[Dict[str, Any]], Any]):
        if not self.channel or not self.exchange:
            return

        try:
            queue = await self.channel.declare_queue(exclusive=True)
            await queue.bind(self.exchange, routing_key)

            async def process_message(message: aio_pika.IncomingMessage):
                async with message.process():
                    body = json.loads(message.body.decode())
                    logger.debug(f"Received event [{routing_key}]: {body}")
                    if asyncio.iscoroutinefunction(callback):
                        await callback(body)
                    else:
                        callback(body)

            await queue.consume(process_message)
            logger.info(f"Subscribed to events: {routing_key}")
        except Exception as e:
            logger.error(f"Error subscribing to {routing_key}")

    async def close(self):
        if self.connection:
            await self.connection.close()


event_bus = EventBus()
