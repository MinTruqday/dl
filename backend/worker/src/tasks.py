import os
import subprocess
import tempfile
import httpx
from celery import Celery
from kombu import Exchange, Queue
from core.config import settings
from loguru import logger

CELERY_BROKER_URL = settings.RABBITMQ_URI
CELERY_RESULT_BACKEND = settings.REDIS_URI

celery_app = Celery("doclib_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

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
        queue_arguments={"x-dead-letter-exchange": "dlx", "x-dead-letter-routing-key": "dlq"},
    ),
    Queue("dlq", Exchange("dlx"), routing_key="dlq"),
)

@celery_app.task(name="src.tasks.hard_delete_document", acks_late=True, reject_on_worker_lost=True, max_retries=3, default_retry_delay=10)
def hard_delete_document(document_id: str, user_id: str):
    logger.info(f"Bắt đầu xóa vĩnh viễn dữ liệu vector tài liệu {document_id}")
    try:
        rag_url = settings.AGENTIC_AI_URL
        if rag_url:
            response = httpx.delete(f"{rag_url}/suy-luan/vector/{document_id}", timeout=settings.DEFAULT_HTTP_TIMEOUT)
            response.raise_for_status()
        logger.info(f"Đã xóa thành công dữ liệu vector tài liệu {document_id}")
    except Exception as e:
        logger.error(f"Lỗi mạng: Không thể xóa dữ liệu vector của tài liệu {document_id}")
        raise hard_delete_document.retry(exc=e)

@celery_app.task(name="src.tasks.compile_document_tectonic", acks_late=True, reject_on_worker_lost=True, max_retries=2, default_retry_delay=10)
def compile_document_tectonic(document_id: str, tex_content: str):
    logger.info(f"Bắt đầu biên dịch LaTeX cho tài liệu {document_id}")
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, f"{document_id}.tex")
        pdf_path = os.path.join(temp_dir, f"{document_id}.pdf")
        log_path = os.path.join(temp_dir, f"{document_id}.log")

        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)

        try:
            logger.debug(f"Bắt đầu biên dịch tài liệu")
            process = subprocess.run(
                ["tectonic", "--synctex", "--keep-logs", "-Z", "continue-on-errors", "--outdir", temp_dir, tex_path],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if not os.path.exists(pdf_path):
                logger.error(f"Không thể tạo file PDF cho tài liệu")
                log_content = process.stdout + process.stderr
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8") as lf:
                        log_content += "\n" + lf.read()
                return {
                    "status": "error",
                    "error": "Lỗi biên dịch không thể tạo file PDF",
                    "logs": log_content,
                    "document_id": document_id,
                }

            logger.info(f"Tài liệu {document_id} đã biên dịch xong và tạo PDF")
            return {"status": "success", "pdf_path": pdf_path, "document_id": document_id, "logs": process.stdout}

        except subprocess.TimeoutExpired:
            logger.error(f"Quá trình biên dịch vượt quá thời gian cho phép với tài liệu {document_id}")
            return {
                "status": "error",
                "error": "Lỗi quá thời gian biên dịch tài liệu",
                "document_id": document_id,
            }
        except Exception as e:
            logger.exception(f"Lỗi hệ thống không mong muốn khi biên dịch tài liệu {document_id}")
            return {
                "status": "error",
                "error": "Lỗi hệ thống không xác định khi biên dịch",
                "document_id": document_id,
            }