import json

from aio_pika import DeliveryMode, Message
from loguru import logger

from src.core.infrastructure.database import database


async def publish_compile_task(document_id: str, creator_id: str, content_raw: str):
    if not database.rabbitmq:
        logger.error("Lỗi kết nối hàng đợi tác vụ nền")
        return False

    try:
        async with database.rabbitmq.channel() as channel:
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
        logger.error(f"Lỗi khởi tạo quá trình biên dịch: {e}")
        return False


async def trigger_document_publish_job(document_id: str, creator_id: str):
    if not database.rabbitmq:
        logger.error("Lỗi kết nối hàng đợi tác vụ nền")
        return False

    try:
        async with database.rabbitmq.channel() as channel:
            queue = await channel.declare_queue("document_publish_queue", durable=True)

            payload = {"document_id": document_id, "creator_id": creator_id}

            message = Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
            )

            await channel.default_exchange.publish(message, routing_key=queue.name)
            return True
    except Exception as e:
        logger.error(f"Lỗi khởi tạo quá trình xuất bản: {e}")
        return False


async def publish_event(queue_name: str, payload: dict):
    if not database.rabbitmq:
        logger.error("Lỗi kết nối hàng đợi tác vụ nền")
        return False

    try:
        async with database.rabbitmq.channel() as channel:
            queue = await channel.declare_queue(queue_name, durable=True)
            message = Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT,
            )
            await channel.default_exchange.publish(message, routing_key=queue.name)
            return True
    except Exception as e:
        logger.error(f"Lỗi xuất bản sự kiện: {e}")
        return False
