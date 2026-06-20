import os
import subprocess
import tempfile

from celery import Celery
from core.config import settings
from loguru import logger

CELERY_BROKER_URL = settings.RABBITMQ_URI
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
    logger.info("Đang bắt đầu quá trình xóa vĩnh viễn tài liệu")
    import httpx

    try:
        from core.database import db_client

        rag_url = settings.AGENTIC_AI_URL
        if rag_url:
            httpx.delete(
                f"{rag_url}/inference/vector/{document_id}",
                timeout=settings.DEFAULT_HTTP_TIMEOUT,
            )
        logger.info("Xóa vĩnh viễn tài liệu thành công")
    except Exception as e:
        logger.error("Lỗi xóa vĩnh viễn tài liệu")
        raise hard_delete_document_task.retry(exc=e)


@celery_app.task(
    name="src.tasks.compile_document_tectonic",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=2,
    default_retry_delay=10,
)
def compile_document_tectonic(document_id, tex_content):
    logger.info("Đang bắt đầu quá trình biên dịch tài liệu")
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, f"{document_id}.tex")
        pdf_path = os.path.join(temp_dir, f"{document_id}.pdf")
        log_path = os.path.join(temp_dir, f"{document_id}.log")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        try:
            logger.debug("Đang thực thi biên dịch tài liệu")
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
                logger.error("Lỗi biên dịch, không thể tạo kết quả cuối cùng")
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

            logger.info("Biên dịch tài liệu thành công")

            return {
                "status": "success",
                "pdf_path": pdf_path,
                "document_id": document_id,
                "logs": process.stdout,
            }
        except subprocess.TimeoutExpired:
            logger.error("Quá thời gian biên dịch tài liệu")
            return {
                "status": "error",
                "error": "Quá thời gian biên dịch, vui lòng kiểm tra cấu trúc tài liệu",
                "document_id": document_id,
            }
        except Exception as e:
            logger.exception("Lỗi hệ thống khi biên dịch tài liệu")
            return {
                "status": "error",
                "error": "Lỗi xử lý tài liệu, vui lòng thử lại sau",
                "document_id": document_id
            }