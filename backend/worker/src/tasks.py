from celery import Celery
import os
import subprocess
import tempfile
from loguru import logger

CELERY_BROKER_URL = os.environ.get("RABBITMQ_URI")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URI")

celery_app = Celery("doclib_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery_app.task(name="src.tasks.convert_and_send_to_kindle")
def convert_and_send_to_kindle(document_id, kindle_email, original_format):
    logger.info(f"Task: convert_and_send_to_kindle for document {document_id}")
    return {"status": "success", "document_id": document_id, "kindle_email": kindle_email}

@celery_app.task(name="src.tasks.compile_document_tectonic")
def compile_document_tectonic(document_id, tex_content):
    logger.info(f"Task: compile_document_tectonic started for document {document_id}")
    temp_dir = tempfile.gettempdir()
    tex_path = os.path.join(temp_dir, f"{document_id}.tex")
    pdf_path = os.path.join(temp_dir, f"{document_id}.pdf")
    log_path = os.path.join(temp_dir, f"{document_id}.log")
    
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_content)
        
    try:
        logger.debug(f"Running Tectonic for document {document_id}")
        process = subprocess.run(
            ["tectonic", "--synctex", "--keep-logs", "-Z", "continue-on-errors", "-Z", "shell-escape", "--outdir", temp_dir, tex_path],
            capture_output=True,
            text=True
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
    except Exception as e:
        logger.exception(f"Error in compile_document_tectonic: {e}")
        return {"status": "error", "error": str(e), "document_id": document_id}

