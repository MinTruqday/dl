from celery import Celery
import os
import subprocess
import tempfile
from loguru import logger

from core.config import settings

CELERY_BROKER_URL = settings.RABBITMQ_URI
CELERY_RESULT_BACKEND = settings.REDIS_URI

celery_app = Celery("doclib_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery_app.task(name="src.tasks.compile_document_tectonic")
def compile_document_tectonic(document_id, tex_content):
    logger.info(f"Task: compile_document_tectonic started for document {document_id}")
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_path = os.path.join(temp_dir, f"{document_id}.tex")
        pdf_path = os.path.join(temp_dir, f"{document_id}.pdf")
        log_path = os.path.join(temp_dir, f"{document_id}.log")
        
        with open(tex_path, "w", encoding="utf-8") as f:
            f.write(tex_content)
            
        try:
            logger.debug(f"Running Tectonic for document {document_id}")
            process = subprocess.run(
                ["tectonic", "--synctex", "--keep-logs", "-Z", "continue-on-errors", "--outdir", temp_dir, tex_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if not os.path.exists(pdf_path):
                logger.error(f"Tectonic compilation failed for document {document_id}")
                log_content = process.stdout + process.stderr
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8") as lf:
                        log_content += "\n" + lf.read()
                return {"status": "error", "error": "Compilation failed", "logs": log_content, "document_id": document_id}
                
            logger.info(f"Task: compile_document_tectonic completed successfully for document {document_id}")
            
            return {"status": "success", "pdf_path": pdf_path, "document_id": document_id, "logs": process.stdout}
        except subprocess.TimeoutExpired:
            logger.error(f"Tectonic compilation timed out for document {document_id}")
            return {"status": "error", "error": "Quá thời gian biên dịch cho phép (60s). Có thể tài liệu chứa vòng lặp vô hạn.", "document_id": document_id}
        except Exception as e:
            logger.exception(f"Error in compile_document_tectonic: {e}")
            return {"status": "error", "error": str(e), "document_id": document_id}
