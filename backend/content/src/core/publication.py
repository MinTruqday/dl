from src.core.infrastructure.mq import mq

async def publish_compile_task(document_id: str, creator_id: str, content_raw: str, job_id: str):
    payload = {
        "job_id": job_id,
        "document_id": document_id,
        "creator_id": creator_id,
        "content_raw": content_raw,
    }
    return await mq.publish("tectonic_queue", payload)

async def trigger_document_publish_job(document_id: str, creator_id: str, job_id: str):
    payload = {
        "job_id": job_id,
        "document_id": document_id,
        "creator_id": creator_id,
    }
    return await mq.publish("document_publish_queue", payload)

async def publish_event(queue_name: str, payload: dict):
    return await mq.publish(queue_name, payload)
