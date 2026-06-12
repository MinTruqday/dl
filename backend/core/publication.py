import json
from loguru import logger
from aio_pika import Message, DeliveryMode
from core.database import db_client

async def publish_compile_task(document_id: str, author_id: str, content_raw: str):
    if not db_client.rabbitmq:
        logger.error("Lỗi kết nối hệ thống hàng đợi, không thể thêm tác vụ biên dịch vào hàng đợi")
        return False
        
    try:
        async with db_client.rabbitmq.channel() as channel:
            queue = await channel.declare_queue("tectonic_queue", durable=True)
            
            payload = {
                "document_id": document_id,
                "author_id": author_id,
                "content_raw": content_raw
            }
            
            message = Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT
            )
            
            await channel.default_exchange.publish(
                message,
                routing_key=queue.name
            )
            return True
    except Exception as e:
        logger.error(f"Không thể khởi tạo tiến trình của công cụ biên dịch: {str(e)}")
        return False

async def trigger_document_publish_job(document_id: str, author_id: str):
    if not db_client.rabbitmq:
        logger.error("Lỗi kết nối hệ thống hàng đợi, không thể thêm tác vụ xuất bản vào hàng đợi")
        return False
        
    try:
        async with db_client.rabbitmq.channel() as channel:
            queue = await channel.declare_queue("document_publish_queue", durable=True)
            
            payload = {
                "document_id": document_id,
                "author_id": author_id
            }
            
            message = Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT
            )
            
            await channel.default_exchange.publish(
                message,
                routing_key=queue.name
            )
            return True
    except Exception as e:
        logger.error(f"Không thể khởi tạo tiến trình xuất bản: {str(e)}")
        return False

async def publish_event(queue_name: str, payload: dict):
    if not db_client.rabbitmq:
        logger.error("Lỗi kết nối hệ thống hàng đợi, không thể thêm sự kiện vào hàng đợi")
        return False
        
    try:
        async with db_client.rabbitmq.channel() as channel:
            queue = await channel.declare_queue(queue_name, durable=True)
            message = Message(
                body=json.dumps(payload).encode("utf-8"),
                delivery_mode=DeliveryMode.PERSISTENT
            )
            await channel.default_exchange.publish(message, routing_key=queue.name)
            return True
    except Exception as e:
        logger.error(f"Lỗi phát hành sự kiện {queue_name}: {str(e)}")
        return False
