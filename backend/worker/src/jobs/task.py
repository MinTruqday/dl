import asyncio
import json
import re
from contextlib import suppress
from datetime import datetime, timedelta, timezone

import httpx
from loguru import logger

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import record_job
from src.core.infrastructure.mq import mq


IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class PermanentTaskError(Exception):
    code = "permanent_task_error"


def validate_identifier(value: str, field: str):
    if not IDENTIFIER_PATTERN.fullmatch(str(value or "")):
        raise PermanentTaskError(f"Invalid {field}")


async def handle_assessment_calibration(payload: dict):
    job_id = str(payload.get("job_id") or "")
    owner_id = str(payload.get("owner_id") or "")
    owner_email = str(payload.get("owner_email") or "")
    validate_identifier(job_id, "job identifier")
    validate_identifier(owner_id, "owner identifier")
    calibration_payload = payload.get("payload")
    if not isinstance(calibration_payload, dict):
        raise PermanentTaskError("Calibration payload is required")
    await record_job(
        job_id,
        {"status": "running", "attempt_started_at": datetime.now(timezone.utc)},
        {"kind": "assessment_calibration", "owner_id": owner_id},
    )
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{settings.ASSESSMENT_URL}/internal/calibration/run",
            headers={
                "X-Internal-Token": settings.SECRET_KEY,
                "X-Owner-Id": owner_id,
                "X-Owner-Email": owner_email,
            },
            json=calibration_payload,
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


HANDLERS = {"assessment_calibration_queue": handle_assessment_calibration}


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
