import asyncio
import hashlib
import json
import os
import re
import resource
import signal
import tempfile
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database, record_job
from src.core.infrastructure.mq import mq
from src.core.storage import upload_pdf


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
UNSAFE_LATEX = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in [
        r"\\(?:input|include|lstinputlisting|openin|read|newwrite|openout|write|immediate|write18)\b",
        r"\\usepackage\s*\{[^}]*shellesc[^}]*\}",
        r"(?:https?|file|ftp)://",
        r"\\(?:catcode|csname)\b",
    ]
]


class PermanentTaskError(Exception):
    code = "permanent_task_error"


def validate_identifier(value: str, field: str):
    if not IDENTIFIER_PATTERN.fullmatch(str(value or "")):
        raise PermanentTaskError(f"Invalid {field}")


def validate_latex(content: str):
    encoded = content.encode("utf-8")
    if not encoded or len(encoded) > settings.MAX_COMPILE_INPUT_BYTES:
        raise PermanentTaskError("Invalid compilation input size")
    if any(pattern.search(content) for pattern in UNSAFE_LATEX):
        raise PermanentTaskError("Unsafe LaTeX directive")


def limit_process():
    resource.setrlimit(resource.RLIMIT_CPU, (25, 25))
    resource.setrlimit(resource.RLIMIT_AS, (4 * 1024 * 1024 * 1024, 4 * 1024 * 1024 * 1024))
    resource.setrlimit(resource.RLIMIT_FSIZE, (settings.MAX_COMPILE_OUTPUT_BYTES, settings.MAX_COMPILE_OUTPUT_BYTES))
    resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))
    resource.setrlimit(resource.RLIMIT_NPROC, (128, 128))


async def compile_latex(content: str) -> bytes:
    validate_latex(content)
    with tempfile.TemporaryDirectory(prefix="doclib_worker_") as temp_dir:
        tex_path = os.path.join(temp_dir, "main.tex")
        pdf_path = os.path.join(temp_dir, "main.pdf")
        with open(tex_path, "w", encoding="utf-8") as stream:
            stream.write(content)
        process = await asyncio.create_subprocess_exec(
            "tectonic",
            "--untrusted",
            "--outdir",
            temp_dir,
            tex_path,
            cwd=temp_dir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=2 * 1024 * 1024,
            preexec_fn=limit_process,
            start_new_session=True,
        )
        try:
            _, stderr = await asyncio.wait_for(process.communicate(), timeout=30)
        except asyncio.TimeoutError:
            os.killpg(process.pid, signal.SIGKILL)
            await process.wait()
            raise RuntimeError("Compilation timed out")
        if process.returncode != 0 or not os.path.isfile(pdf_path):
            error = stderr.decode("utf-8", errors="ignore")[-1000:]
            raise PermanentTaskError(error or "Compilation failed")
        size = os.path.getsize(pdf_path)
        if size < 1 or size > settings.MAX_COMPILE_OUTPUT_BYTES:
            raise PermanentTaskError("Invalid compilation output size")
        with open(pdf_path, "rb") as stream:
            return stream.read()


def compile_job_id(payload: dict) -> str:
    provided = str(payload.get("job_id") or "")
    if provided:
        validate_identifier(provided, "job identifier")
        return provided
    digest = hashlib.sha256(
        (
            str(payload.get("document_id", ""))
            + "\0"
            + str(payload.get("content_raw", payload.get("tex_content", "")))
        ).encode("utf-8")
    ).hexdigest()
    return f"compile-{digest}"


async def handle_compile(payload: dict):
    document_id = str(payload.get("document_id") or "")
    validate_identifier(document_id, "document identifier")
    content = payload.get("content_raw", payload.get("tex_content"))
    if not isinstance(content, str):
        raise PermanentTaskError("Compilation content is required")
    job_id = compile_job_id(payload)
    jobs = database.mongodb[settings.WORKER_DB_NAME].worker_jobs
    existing = await jobs.find_one({"_id": job_id}, {"status": 1, "result": 1})
    if existing and existing.get("status") == "completed":
        return existing.get("result")
    document = await database.mongodb[settings.CONTENT_DB_NAME].documents.find_one(
        {"_id": document_id},
        {"creator_id": 1},
    )
    creator_id = str(payload.get("creator_id") or (document or {}).get("creator_id") or "system")
    validate_identifier(creator_id, "creator identifier")
    await record_job(
        job_id,
        {"status": "running", "attempt_started_at": datetime.now(timezone.utc)},
        {
            "kind": "compile",
            "document_id": document_id,
            "creator_id": creator_id,
        },
    )
    pdf = await compile_latex(content)
    digest = hashlib.sha256(pdf).hexdigest()
    object_path = f"users/{creator_id}/compiled/{document_id}/{digest}.pdf"
    await upload_pdf(object_path, pdf)
    if document:
        await database.mongodb[settings.CONTENT_DB_NAME].documents.update_one(
            {"_id": document_id, "creator_id": creator_id},
            {
                "$set": {
                    "compiled_file_url": object_path,
                    "compile_status": "completed",
                    "compiled_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
                "$unset": {"compile_error": ""},
            },
        )
    result = {
        "document_id": document_id,
        "file_url": object_path,
        "size": len(pdf),
        "sha256": digest,
    }
    await record_job(
        job_id,
        {
            "status": "completed",
            "result": result,
            "expire_at": datetime.now(timezone.utc) + timedelta(days=7),
        },
    )
    return result


async def handle_publish(payload: dict):
    document_id = str(payload.get("document_id") or "")
    creator_id = str(payload.get("creator_id") or "")
    job_id = str(payload.get("job_id") or "")
    validate_identifier(document_id, "document identifier")
    validate_identifier(creator_id, "creator identifier")
    validate_identifier(job_id, "job identifier")
    await record_job(
        job_id,
        {"status": "running", "attempt_started_at": datetime.now(timezone.utc)},
        {
            "kind": "publish",
            "document_id": document_id,
            "creator_id": creator_id,
        },
    )
    now = datetime.now(timezone.utc)
    result = await database.mongodb[settings.CONTENT_DB_NAME].documents.update_one(
        {
            "_id": document_id,
            "creator_id": creator_id,
            "publication_job_id": job_id,
            "status": "processing_publish",
            "is_deleted": {"$ne": True},
        },
        {
            "$set": {
                "status": "published",
                "published_at": now,
                "updated_at": now,
            },
            "$unset": {
                "publication_job_id": "",
                "publication_error": "",
                "scheduled_publish_at": "",
                "publish_at": "",
            },
        },
    )
    if result.modified_count == 0:
        current = await database.mongodb[settings.CONTENT_DB_NAME].documents.find_one(
            {"_id": document_id},
            {"status": 1, "is_deleted": 1},
        )
        if current and current.get("status") == "published":
            await record_job(
                job_id,
                {
                    "status": "completed",
                    "result": {"document_id": document_id, "status": "published"},
                    "expire_at": now + timedelta(days=7),
                },
            )
            return
        raise PermanentTaskError("Document is not eligible for publication")
    await record_job(
        job_id,
        {
            "status": "completed",
            "result": {"document_id": document_id, "status": "published"},
            "expire_at": now + timedelta(days=7),
        },
    )


HANDLERS = {
    "tectonic_queue": handle_compile,
    "document_publish_queue": handle_publish,
}


async def mark_failed(queue_name: str, payload: dict, error: Exception):
    message = str(error)[-1000:]
    job_id = str(payload.get("job_id") or "")
    if queue_name == "tectonic_queue":
        try:
            job_id = compile_job_id(payload)
        except PermanentTaskError:
            job_id = ""
        document_id = str(payload.get("document_id") or "")
        if IDENTIFIER_PATTERN.fullmatch(document_id):
            await database.mongodb[settings.CONTENT_DB_NAME].documents.update_one(
                {"_id": document_id},
                {
                    "$set": {
                        "compile_status": "failed",
                        "compile_error": message,
                        "updated_at": datetime.now(timezone.utc),
                    }
                },
            )
    if queue_name == "document_publish_queue":
        document_id = str(payload.get("document_id") or "")
        if IDENTIFIER_PATTERN.fullmatch(document_id) and IDENTIFIER_PATTERN.fullmatch(job_id):
            await database.mongodb[settings.CONTENT_DB_NAME].documents.update_one(
                {
                    "_id": document_id,
                    "publication_job_id": job_id,
                    "status": "processing_publish",
                },
                {
                    "$set": {
                        "status": "draft",
                        "publication_error": message,
                        "updated_at": datetime.now(timezone.utc),
                    },
                    "$unset": {
                        "publication_job_id": "",
                        "scheduled_publish_at": "",
                        "publish_at": "",
                    },
                },
            )
    if IDENTIFIER_PATTERN.fullmatch(job_id):
        await record_job(
            job_id,
            {
                "status": "failed",
                "error": message,
                "expire_at": datetime.now(timezone.utc) + timedelta(days=7),
            },
            {
                "kind": queue_name,
                "document_id": str(payload.get("document_id") or ""),
            },
        )


class WorkerRunner:
    def __init__(self):
        self.tasks = []

    async def consume(self, queue_name: str):
        handler = HANDLERS[queue_name]
        while True:
            try:
                queue = await mq.get_queue(queue_name)
                async with queue.iterator() as iterator:
                    async for message in iterator:
                        try:
                            payload = json.loads(message.body.decode("utf-8"))
                            if not isinstance(payload, dict):
                                raise PermanentTaskError("Task payload must be an object")
                        except (UnicodeDecodeError, json.JSONDecodeError, PermanentTaskError):
                            await message.reject(requeue=False)
                            continue
                        failure = None
                        for attempt in range(settings.WORKER_MAX_RETRIES):
                            try:
                                await handler(payload)
                                failure = None
                                break
                            except PermanentTaskError as error:
                                failure = error
                                break
                            except Exception as error:
                                failure = error
                                logger.exception("Worker task attempt failed")
                                if attempt + 1 < settings.WORKER_MAX_RETRIES:
                                    await asyncio.sleep(2 ** attempt)
                        if failure is None:
                            await message.ack()
                        else:
                            await mark_failed(queue_name, payload, failure)
                            if isinstance(failure, PermanentTaskError):
                                await message.ack()
                            else:
                                await message.reject(requeue=False)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Worker queue consumer cycle failed")
                await asyncio.sleep(2)

    async def schedule_publications(self):
        documents = database.mongodb[settings.CONTENT_DB_NAME].documents
        while True:
            try:
                now = datetime.now(timezone.utc)
                job_id = f"publish-{os.urandom(16).hex()}"
                from pymongo import ReturnDocument
                document = await documents.find_one_and_update(
                    {
                        "scheduled_publish_at": {"$lte": now},
                        "status": {"$nin": ["processing_publish", "published"]},
                        "is_deleted": {"$ne": True},
                        "creator_id": {"$type": "string"},
                    },
                    {
                        "$set": {
                            "status": "processing_publish",
                            "publication_job_id": job_id,
                            "updated_at": now,
                        }
                    },
                    return_document=ReturnDocument.AFTER,
                )
                if not document:
                    await asyncio.sleep(15)
                    continue
                payload = {
                    "job_id": job_id,
                    "document_id": str(document["_id"]),
                    "creator_id": str(document["creator_id"]),
                }
                try:
                    await mq.publish("document_publish_queue", payload)
                except Exception:
                    await documents.update_one(
                        {"_id": document["_id"], "publication_job_id": job_id},
                        {
                            "$set": {"status": "draft", "updated_at": now},
                            "$unset": {"publication_job_id": ""},
                        },
                    )
                    raise
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Scheduled publication cycle failed")
                await asyncio.sleep(5)

    async def start(self):
        for attempt in range(1, 11):
            try:
                await mq.connect()
                break
            except Exception:
                if attempt == 10:
                    raise
                logger.warning(
                    "Worker message queue connection delayed attempt={}",
                    attempt,
                )
                await asyncio.sleep(min(attempt, 5))
        self.tasks = [
            asyncio.create_task(self.consume(queue_name), name=f"worker:{queue_name}")
            for queue_name in HANDLERS
        ]
        self.tasks.append(
            asyncio.create_task(
                self.schedule_publications(),
                name="worker:scheduled_publications",
            )
        )

    async def close(self):
        for task in self.tasks:
            task.cancel()
        for task in self.tasks:
            with suppress(asyncio.CancelledError, Exception):
                await task
        self.tasks.clear()

    def is_running(self) -> bool:
        return bool(self.tasks and all(not task.done() for task in self.tasks))


worker_runner = WorkerRunner()
