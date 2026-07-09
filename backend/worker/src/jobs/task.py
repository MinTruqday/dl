import os
import subprocess
import tempfile

import httpx
from celery import Celery
from loguru import logger

from src.core.infrastructure.configuration import settings

CELERY_BROKER_URL = settings.REDIS_URI
CELERY_RESULT_BACKEND = settings.REDIS_URI

from kombu import Exchange, Queue

celery_app = Celery(
    "doclib_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND
)
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.worker_log_format = "%(asctime)s | %(levelname)s | %(message)s"
celery_app.conf.worker_task_log_format = "%(asctime)s | %(levelname)s | %(message)s"
celery_app.conf.worker_log_color = False

celery_app.conf.task_queues = (
    Queue(
        "celery",
        Exchange("celery"),
        routing_key="celery",
        queue_arguments={
            "x-dead-letter-exchange": "dlx",
            "x-dead-letter-routing-key": "dlq",
        },
    ),
    Queue("dlq", Exchange("dlx"), routing_key="dlq"),
)

@celery_app.task(
    name="src.tasks.hard_delete_document_task",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=3,
    default_retry_delay=10,
)
def hard_delete_document_task(document_id: str, user_id: str):
    logger.info("Starting hard deletion process for document")
    try:
        from src.core.infrastructure.database import database

        rag_url = settings.AGENTIC_AI_URL
        if rag_url:
            httpx.delete(
                f"{rag_url}/inference/vector/{document_id}",
                timeout=settings.DEFAULT_HTTP_TIMEOUT,
            )
        logger.info("Hard deletion process for document completed successfully")
    except Exception as e:
        logger.exception("Failed to execute hard deletion process for document")
        raise hard_delete_document_task.retry(exc=e)

@celery_app.task(
    name="src.tasks.compile_document_tectonic",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=2,
    default_retry_delay=10,
)
def compile_document_tectonic(document_id, tex_content):
    logger.info("Starting Tectonic compilation process for document")
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, f"{document_id}.tex")
        pdf_path = os.path.join(temp_dir, f"{document_id}.pdf")
        log_path = os.path.join(temp_dir, f"{document_id}.log")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        try:
            logger.debug("Executing Tectonic compilation binary")
            process = subprocess.run(
                [
                    "tectonic",
                    "--synctex",
                    "--keep-logs",
                    "-Z",
                    "continue-on-errors",
                    "--outdir",
                    temp_dir,
                    tex_path,
                ],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if not os.path.exists(pdf_path):
                logger.error("Failed to generate output PDF file")
                log_content = process.stdout + process.stderr
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8") as lf:
                        log_content += "\n" + lf.read()
                return {
                    "status": "error",
                    "error": "Lỗi định dạng cấu trúc tài liệu",
                    "logs": log_content,
                    "document_id": document_id,
                }

            logger.info("Tectonic compilation process completed successfully")

            return {
                "status": "success",
                "pdf_path": pdf_path,
                "document_id": document_id,
                "logs": process.stdout,
            }
        except subprocess.TimeoutExpired as e:
            logger.exception("Compilation process timed out")
            return {
                "status": "error",
                "error": "Quá thời gian biên dịch, vui lòng kiểm tra cấu trúc tài liệu",
                "document_id": document_id,
            }
        except Exception as e:
            logger.exception("Unexpected error during Tectonic compilation")
            return {
                "status": "error",
                "error": "Xử lý tài liệu thất bại, vui lòng thử lại sau",
                "document_id": document_id,
            }

@celery_app.task(
    name="src.tasks.compress_file_task",
    acks_late=True,
    reject_on_worker_lost=True,
)
def compress_file_task(file_path: str, mime_type: str):
    import asyncio
    import brotli
    import aioboto3
    
    MINIO_ENDPOINT = settings.MINIO_ENDPOINT
    MINIO_ACCESS_KEY = settings.MINIO_ACCESS_KEY
    MINIO_SECRET_KEY = settings.MINIO_SECRET_KEY
    MINIO_PRIVATE_BUCKET = settings.MINIO_PRIVATE_BUCKET
    MINIO_PUBLIC_BUCKET = settings.MINIO_PUBLIC_BUCKET

    def get_bucket(path: str) -> str:
        if path.startswith("system/"):
            return MINIO_PRIVATE_BUCKET
        return MINIO_PUBLIC_BUCKET

    async def _compress():
        session = aioboto3.Session()
        async with session.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
        ) as storage_client:
            logger.info(f"Downloading {file_path} for compression")
            target_bucket = get_bucket(file_path)
            response = await storage_client.get_object(
                Bucket=target_bucket, Key=file_path
            )
            content = await response["Body"].read()
            
            if response.get("ContentEncoding") == "br":
                logger.info(f"File {file_path} is already compressed")
                return

            logger.info(f"Compressing {file_path}")
            compressed_content = brotli.compress(content, quality=11)
            
            logger.info(f"Uploading compressed {file_path}")
            await storage_client.put_object(
                Bucket=target_bucket,
                Key=file_path,
                Body=compressed_content,
                ContentType=mime_type,
                ContentEncoding="br"
            )
            logger.info(f"Successfully compressed {file_path}")

    asyncio.run(_compress())
    return {"status": "success", "file_path": file_path}
