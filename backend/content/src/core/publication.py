import json
from loguru import logger
from src.core.infrastructure.queue_client import queue_client

async def publish_compile_task(document_id: str, creator_id: str, content_raw: str):
    payload = {
        "document_id": document_id,
        "creator_id": creator_id,
        "content_raw": content_raw,
    }
    return await queue_client.publish("tectonic_queue", payload)

async def trigger_document_publish_job(document_id: str, creator_id: str):
    payload = {"document_id": document_id, "creator_id": creator_id}
    return await queue_client.publish("document_publish_queue", payload)

async def publish_event(queue_name: str, payload: dict):
    return await queue_client.publish(queue_name, payload)
