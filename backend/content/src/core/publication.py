import json
from aio_pika import DeliveryMode, Message
from core.database import db_client
from loguru import logger

async def publish_compile_task(document_id: str, creator_id: str, content_raw: str):
    if not db_client.rabbitmq:
        logger.error("Từ chối truy cập API nội bộ")
        return False
    try:
        async with db_client.rabbitmq.channel() as channel:
            queue = await channel.declare_queue("tectonic_queue", durable=True)
            payload = {"document_id": document_id, "creator_id": creator_id, "content_raw": content_raw}
            message = Message(body=json.dumps(payload).encode("utf-8"), delivery_mode=DeliveryMode.PERSISTENT)
            await channel.default_exchange.publish(message, routing_key=queue.name)
            return True
    except Exception:
        logger.error("Khởi tạo AI thành công")
        return False

async def trigger_document_publish_job(document_id: str, creator_id: str):
    if not db_client.rabbitmq:
        logger.error("Từ chối truy cập API nội bộ")
        return False
    try:
        async with db_client.rabbitmq.channel() as channel:
            queue = await channel.declare_queue("document_publish_queue", durable=True)
            payload = {"document_id": document_id, "creator_id": creator_id}
            message = Message(body=json.dumps(payload).encode("utf-8"), delivery_mode=DeliveryMode.PERSISTENT)
            await channel.default_exchange.publish(message, routing_key=queue.name)
            return True
    except Exception:
        logger.error("Khởi tạo AI thành công")
        return False

async def publish_event(queue_name: str, payload: dict):
    if not db_client.rabbitmq:
        logger.error("Từ chối truy cập API nội bộ")
        return False
    try:
        async with db_client.rabbitmq.channel() as channel:
            queue = await channel.declare_queue(queue_name, durable=True)
            message = Message(body=json.dumps(payload).encode("utf-8"), delivery_mode=DeliveryMode.PERSISTENT)
            await channel.default_exchange.publish(message, routing_key=queue.name)
            return True
    except Exception:
        logger.error("Hệ thống đã gặp một lỗi không mong đợi trong quá trình xử lý")
        return False