from celery import Celery
import os
import subprocess

CELERY_BROKER_URL = os.environ.get("RABBITMQ_URI")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URI")

celery_app = Celery("doclib_tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery_app.task(name="src.tasks.convert_and_send_to_kindle")
def convert_and_send_to_kindle(document_id, kindle_email, original_format):
    return {"status": "success", "document_id": document_id, "kindle_email": kindle_email}

@celery_app.task(name="src.tasks.compile_document_tectonic")
def compile_document_tectonic(document_id, tex_content):
    tex_path = f"/tmp/{document_id}.tex"
    pdf_path = f"/tmp/{document_id}.pdf"
    log_path = f"/tmp/{document_id}.log"
    with open(tex_path, "w") as f:
        f.write(tex_content)
    try:
        process = subprocess.run(
            ["tectonic", "--synctex", "--keep-logs", "-Z", "continue-on-errors", "-Z", "shell-escape", "--outdir", "/tmp/", tex_path],
            capture_output=True,
            text=True
        )
        if not os.path.exists(pdf_path):
            log_content = process.stdout + process.stderr
            if os.path.exists(log_path):
                with open(log_path, "r") as lf:
                    log_content += "\n" + lf.read()
            return {"status": "error", "error": "Biên dịch thất bại", "logs": log_content, "document_id": document_id}
        return {"status": "success", "pdf_path": pdf_path, "document_id": document_id, "logs": process.stdout}
    except Exception as e:
        return {"status": "error", "error": str(e), "document_id": document_id}

