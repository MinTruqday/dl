import asyncio
import hashlib
import hmac
import json
import re
import tempfile
from contextlib import suppress
from datetime import datetime, timedelta, timezone

import httpx
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database, record_job
from src.core.infrastructure.mq import mq
from src.core.metrics import metrics_collector


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class PermanentTaskError(Exception):
    code = "permanent_task_error"


def validate_identifier(value: str, field: str):
    if not IDENTIFIER_PATTERN.fullmatch(str(value or "")):
        raise PermanentTaskError(f"Invalid {field}")


async def handle_qa_job(payload: dict):
    job_id = str(payload.get("job_id") or "")
    requester_id = str(payload.get("requester_id") or "")
    requester_email = str(payload.get("requester_email") or "")
    validate_identifier(job_id, "job identifier")
    validate_identifier(requester_id, "requester identifier")
    job = await database.mongodb[settings.WORKER_DB_NAME].worker_jobs.find_one({"_id": job_id}, {"status": 1})
    if job and job.get("status") == "canceled":
        return
    job_payload = payload.get("payload")
    if not isinstance(job_payload, dict):
        raise PermanentTaskError("QA job payload is required")
    await record_job(
        job_id,
        {"status": "running", "attempt_started_at": datetime.now(timezone.utc)},
        {"kind": payload.get("event"), "project_id": payload.get("project_id"), "requester_id": requester_id},
    )
    if payload.get("event") == "automation.newman.requested":
        result = await run_newman(job_id, payload, job_payload)
        completed_at = datetime.now(timezone.utc)
        await record_job(
            job_id,
            {
                "status": "completed",
                "result": result,
                "completed_at": completed_at,
                "expire_at": completed_at + timedelta(days=30),
            },
        )
        return result
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{settings.TESTING_URL}/kiem-thu/noi-bo/tac-vu/{payload.get('event')}",
            headers={
                "X-Internal-Token": settings.SECRET_KEY,
                "X-Requester-Id": requester_id,
                "X-Requester-Email": requester_email,
            },
            json={"job_id": job_id, "project_id": payload.get("project_id"), "artifact_version_id": payload.get("artifact_version_id"), "model_version": payload.get("model_version"), "payload": job_payload},
        )
    response.raise_for_status()
    result = response.json()
    completed_at = datetime.now(timezone.utc)
    await record_job(
        job_id,
        {
            "status": "completed",
            "result": result,
            "completed_at": completed_at,
            "expire_at": completed_at + timedelta(days=30),
        },
    )
    return result


async def run_newman(job_id, payload, job_payload):
    execution_id = str(job_payload.get("execution_id") or "")
    collection = job_payload.get("collection")
    validate_identifier(execution_id, "automation execution identifier")
    if not isinstance(collection, dict):
        raise PermanentTaskError("Postman collection is required")
    with tempfile.TemporaryDirectory(prefix="veriq-newman-") as directory:
        collection_path = f"{directory}/collection.json"
        report_path = f"{directory}/report.json"
        with open(collection_path, "w", encoding="utf-8") as stream:
            json.dump(collection, stream, ensure_ascii=False)
        process = await asyncio.create_subprocess_exec(
            "newman",
            "run",
            collection_path,
            "--reporters",
            "json",
            "--reporter-json-export",
            report_path,
            "--timeout-request",
            "30000",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        try:
            return_code = await asyncio.wait_for(process.wait(), timeout=900)
        except TimeoutError:
            process.kill()
            await process.wait()
            return_code = 124
        try:
            with open(report_path, encoding="utf-8") as stream:
                report = json.load(stream)
        except (OSError, json.JSONDecodeError):
            report = {}
    run = report.get("run") if isinstance(report.get("run"), dict) else {}
    stats = run.get("stats") if isinstance(run.get("stats"), dict) else {}
    executions = run.get("executions") if isinstance(run.get("executions"), list) else []
    results = []
    for execution in executions[:100000]:
        item = execution.get("item") if isinstance(execution.get("item"), dict) else {}
        response = execution.get("response") if isinstance(execution.get("response"), dict) else {}
        assertions = execution.get("assertions") if isinstance(execution.get("assertions"), list) else []
        results.append(
            {
                "name": str(item.get("name") or "")[:500],
                "status_code": response.get("code"),
                "response_time_ms": response.get("responseTime"),
                "assertions": [
                    {
                        "name": str(assertion.get("assertion") or "")[:500],
                        "passed": not bool(assertion.get("error")),
                    }
                    for assertion in assertions[:1000]
                    if isinstance(assertion, dict)
                ],
            }
        )
    status = "COMPLETED" if return_code == 0 else "FAILED"
    signature_value = f"{execution_id}:{job_id}:{status}"
    callback = {
        "execution_id": execution_id,
        "operation_id": job_id,
        "status": status,
        "summary": {"return_code": return_code, "stats": stats},
        "results": results,
        "logs": ["Newman hoàn tất" if return_code == 0 else "Newman kết thúc với lỗi"],
        "artifact_refs": [],
        "context_signature": hmac.new(
            settings.SECRET_KEY.encode(), signature_value.encode(), hashlib.sha256
        ).hexdigest(),
    }
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{settings.TESTING_URL}/noi-bo/kiem-thu/thuc-thi-tu-dong/ket-qua",
            headers={"X-Internal-Token": settings.SECRET_KEY},
            json=callback,
        )
        response.raise_for_status()
    return {"execution_id": execution_id, "status": status, "summary": callback["summary"]}


HANDLERS = {"qa_job_queue": handle_qa_job}


async def mark_failed(queue_name: str, payload: dict, error: Exception):
    message = str(error)[-1000:]
    job_id = str(payload.get("job_id") or "")
    if IDENTIFIER_PATTERN.fullmatch(job_id):
        completed_at = datetime.now(timezone.utc)
        await record_job(
            job_id,
            {
                "status": "failed",
                "error_code": getattr(error, "code", "worker_task_failed"),
                "error": message,
                "completed_at": completed_at,
                "expire_at": completed_at + timedelta(days=30),
            },
            {"kind": queue_name},
        )


class WorkerRunner:
    def __init__(self):
        self.tasks = []

    async def consume(self, queue_name: str):
        handler = HANDLERS[queue_name]
        while True:
            channel = None
            try:
                channel, queue = await mq.create_consumer_queue(queue_name)
                async with queue.iterator() as iterator:
                    async for message in iterator:
                        try:
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
                                        await asyncio.sleep(2**attempt)
                            if failure is None:
                                await message.ack()
                            else:
                                await mark_failed(queue_name, payload, failure)
                                if isinstance(failure, PermanentTaskError):
                                    await message.ack()
                                else:
                                    await message.reject(requeue=False)
                            metrics_collector.change_queue_depth(queue_name, -1)
                        except Exception:
                            if not message.processed:
                                await message.reject(requeue=True)
                            raise
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Worker queue consumer cycle failed")
                await asyncio.sleep(2)
            finally:
                if channel and not channel.is_closed:
                    await channel.close()

    async def start(self):
        for attempt in range(1, 11):
            try:
                await mq.connect()
                break
            except Exception:
                if attempt == 10:
                    raise
                logger.warning("Worker message queue connection delayed attempt={}", attempt)
                await asyncio.sleep(min(attempt, 5))
        self.tasks = [
            asyncio.create_task(self.consume(queue_name), name=f"worker:{queue_name}")
            for queue_name in HANDLERS
        ]

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
