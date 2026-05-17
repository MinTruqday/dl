import asyncio
import json
import base64
import os
import uuid
import tempfile
import re
from loguru import logger
import aio_pika
import redis.asyncio as redis

from core.config import settings

RABBITMQ_URL = settings.RABBITMQ_URI
REDIS_URL = settings.REDIS_URI

from src.pipelines.tectonic import run_tectonic_compile
from src.pipelines.pandoc import run_pandoc_export

async def process_compilation(message: aio_pika.IncomingMessage, r: redis.Redis):
    async with message.process():
        try:
            payload = json.loads(message.body.decode())
            job_id = payload.get("job_id")
            if not job_id:
                return
                
            task_type = payload.get("type", "compile_preview")
            logger.info(f"Processing job {job_id} of type {task_type}")
            
            if task_type == "compile_preview":
                result = await run_tectonic_compile(job_id, payload.get("content", ""))
            elif task_type == "export_document":
                result = await run_pandoc_export(job_id, payload.get("content", ""), payload.get("format", "docx"))
            else:
                result = {"status": "error", "message": "Task type not supported yet."}
                
            await r.rpush(f"job_result:{job_id}", json.dumps(result))
            await r.expire(f"job_result:{job_id}", 60)
            
            logger.info(f"Finished job {job_id}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")

async def main():
    logger.info("Initializing Compiler Service...")
    r = await redis.from_url(REDIS_URL)
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=5)
    
    queue = await channel.declare_queue("tectonic_queue", durable=True)
    await queue.consume(lambda m: process_compilation(m, r))
    
    logger.info("Compiler Service is listening to tectonic_queue")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
