import json

from aio_pika import DeliveryMode, Message
from loguru import logger

from core.infrastructure.database_client import db_client


async def publish_compile_task(document_id: str, creator_id: str, content_raw: str):
    if not db_client.rabbitmq:
        logger.error("Lỗi kết nối hàng đợi tác vụ nền")
        return False

    try:
        async with db_client.rabbitmq.channel() as channel:
            queue = await channel.declare_queue("tectonic_queue", durable=True)

            payload = {
                "document_id": document_id,
                "creator_id": creator_id,
                "content_raw": content_raw,
            }

            message = Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
            )

            await channel.default_exchange.publish(message, routing_key=queue.name)
            return True
    except Exception as e:
        logger.error("Lỗi khởi tạo quá trình biên dịch")
        return False


async def trigger_document_publish_job(document_id: str, creator_id: str):
    if not db_client.rabbitmq:
        logger.error("Lỗi kết nối hàng đợi tác vụ nền")
        return False

    try:
        async with db_client.rabbitmq.channel() as channel:
            queue = await channel.declare_queue("document_publish_queue", durable=True)

            payload = {"document_id": document_id, "creator_id": creator_id}

            message = Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
            )

            await channel.default_exchange.publish(message, routing_key=queue.name)
            return True
    except Exception as e:
        logger.error("Lỗi khởi tạo quá trình xuất bản")
        return False


async def publish_event(queue_name: str, payload: dict):
    if not db_client.rabbitmq:
        logger.error("Lỗi kết nối hàng đợi tác vụ nền")
        return False

    try:
        async with db_client.rabbitmq.channel() as channel:
            queue = await channel.declare_queue(queue_name, durable=True)
            message = Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
            )
            await channel.default_exchange.publish(message, routing_key=queue.name)
            return True
    except Exception as e:
        logger.error("Lỗi xuất bản sự kiện")
        return False
