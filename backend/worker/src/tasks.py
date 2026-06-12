from celery import Celery
import os
import subprocess
import tempfile
from loguru import logger

from core.config import settings

CELERY_BROKER_URL = settings.RABBITMQ_URI
CELERY_RESULT_BACKEND = settings.REDIS_URI

from kombu import Exchange, Queue

celery_app = Celery("doclib_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
celery_app.conf.worker_log_format = "%(asctime)s | %(levelname)s | %(message)s"
celery_app.conf.worker_task_log_format = "%(asctime)s | %(levelname)s | %(message)s"
celery_app.conf.worker_log_color = False

celery_app.conf.task_queues = (
    Queue('celery', Exchange('celery'), routing_key='celery',
          queue_arguments={'x-dead-letter-exchange': 'dlx',
                           'x-dead-letter-routing-key': 'dlq'}),
    Queue('dlq', Exchange('dlx'), routing_key='dlq'),
)

@celery_app.task(
    name="src.tasks.hard_delete_document_task",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=3,
    default_retry_delay=10
)
def hard_delete_document_task(document_id: str, user_id: str):
    logger.info(f"Đang bắt đầu quá trình xóa hoàn toàn tài liệu {document_id}")
    import httpx
    try:
        from core.database import db_client
        rag_url = settings.AGENTIC_AI_URL
        if rag_url:
            httpx.delete(f"{rag_url}/inference/vector/{document_id}", timeout=10)
        logger.info(f"Tài liệu {document_id} đã được dọn dẹp và xóa hoàn toàn khỏi hệ thống")
    except Exception as e:
        logger.error(f"Không thể xóa hoàn toàn tài liệu {document_id} do lỗi {e}")
        raise hard_delete_document_task.retry(exc=e)

@celery_app.task(
    name="src.tasks.compile_document_tectonic",
    acks_late=True,
    reject_on_worker_lost=True,
    max_retries=2,
    default_retry_delay=10
)
def compile_document_tectonic(document_id, tex_content):
    logger.info(f"Đang khởi động Tectonic để xử lý tài liệu {document_id}")
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, f"{document_id}.tex")
        pdf_path = os.path.join(temp_dir, f"{document_id}.pdf")
        log_path = os.path.join(temp_dir, f"{document_id}.log")
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)
            
        try:
            logger.debug(f"Hệ thống đang sử dụng Tectonic để biên dịch tài liệu {document_id}")
            process = subprocess.run(
                ["tectonic", "--synctex", "--keep-logs", "-Z", "continue-on-errors", "--outdir", temp_dir, tex_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if not os.path.exists(pdf_path):
                logger.error(f"Thất bại khi biên dịch tài liệu {document_id} bằng Tectonic")
                log_content = process.stdout + process.stderr
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8") as lf:
                        log_content += "\n" + lf.read()
                return {"status": "error", "error": "Biên dịch thất bại", "logs": log_content, "document_id": document_id}
                
            logger.info(f"Tectonic đã thành công quá trình biên dịch tài liệu {document_id}")
            
            return {"status": "success", "pdf_path": pdf_path, "document_id": document_id, "logs": process.stdout}
        except subprocess.TimeoutExpired:
            logger.error(f"Tài liệu {document_id} mất quá nhiều thời gian để biên dịch bằng Tectonic")
            return {"status": "error", "error": "Quá thời gian biên dịch cho phép, có thể tài liệu chứa vòng lặp vô hạn", "document_id": document_id}
        except Exception as e:
            logger.exception(f"Lỗi biên dịch Tectonic: {e}")
            return {"status": "error", "error": str(e), "document_id": document_id}
