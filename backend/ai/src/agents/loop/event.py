import asyncio
from uuid6 import uuid7
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional

from loguru import logger
from src.utils.background import create_background_task


class EventType(str, Enum):
    CRON = "cron"
    WEBHOOK = "webhook"
    DOCUMENT_UPLOADED = "document_uploaded"
    USER_QUERY = "user_query"
    SYSTEM_HEARTBEAT = "system_heartbeat"
    DOCUMENT_DELETED = "document_deleted"
    USER_REGISTERED = "user_registered"


@dataclass
class AgentEvent:
    event_id: str
    event_type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processed: bool = False
    processing_result: Optional[str] = None
    error: Optional[str] = None


@dataclass
class SystemUpdate:
    update_id: str
    event_id: str
    update_type: str
    description: str
    applied_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True


EventHandlerCallable = Callable[[AgentEvent], Coroutine[Any, Any, Optional[str]]]


@dataclass
class EventHandler:
    event_type: EventType
    handler: EventHandlerCallable
    description: str = ""
    enabled: bool = True


@dataclass
class CronSchedule:
    schedule_id: str
    name: str
    cron_expression: str
    interval_seconds: int
    event_type: EventType
    payload_template: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    last_run_at: Optional[datetime] = None
    run_count: int = 0
    _task: Optional[asyncio.Task] = field(default=None, repr=False)


class CronScheduler:
    def __init__(self):
        self._schedules: Dict[str, CronSchedule] = {}
        self._event_loop_ref: Optional["EventDrivenLoop"] = None
        self._running = False

    def register(self, schedule: CronSchedule):
        self._schedules[schedule.schedule_id] = schedule
        logger.info(
            f"CronScheduler registered schedule '{schedule.name}' (every {schedule.interval_seconds}s)"
        )

    def unregister(self, schedule_id: str):
        schedule = self._schedules.pop(schedule_id, None)
        if schedule and schedule._task:
            schedule._task.cancel()
        logger.info(f"CronScheduler unregistered schedule {schedule_id}")

    def set_enabled(self, schedule_id: str, enabled: bool):
        schedule = self._schedules[schedule_id]
        schedule.enabled = enabled
        if not enabled:
            if schedule._task and not schedule._task.done():
                schedule._task.cancel()
            schedule._task = None
        elif self._running and (not schedule._task or schedule._task.done()):
            schedule._task = asyncio.create_task(
                self._run_schedule(schedule), name=f"cron:{schedule.name}"
            )

    def set_event_loop(self, event_driven_loop: "EventDrivenLoop"):
        self._event_loop_ref = event_driven_loop

    def list_schedules(self) -> List[Dict]:
        return [
            {
                "schedule_id": s.schedule_id,
                "name": s.name,
                "interval_seconds": s.interval_seconds,
                "event_type": s.event_type.value,
                "enabled": s.enabled,
                "last_run_at": s.last_run_at.isoformat() if s.last_run_at else None,
                "run_count": s.run_count,
            }
            for s in self._schedules.values()
        ]

    async def start(self):
        self._running = True
        for schedule in self._schedules.values():
            if schedule.enabled:
                schedule._task = asyncio.create_task(
                    self._run_schedule(schedule), name=f"cron:{schedule.name}"
                )
        logger.info(f"CronScheduler started {len(self._schedules)} schedules")

    async def stop(self):
        self._running = False
        for schedule in self._schedules.values():
            if schedule._task and not schedule._task.done():
                schedule._task.cancel()
        logger.info("CronScheduler stopped all schedules")

    async def _run_schedule(self, schedule: CronSchedule):
        while self._running and schedule.enabled:
            try:
                await asyncio.sleep(schedule.interval_seconds)
                if not self._running or not schedule.enabled:
                    break

                schedule.last_run_at = datetime.now(timezone.utc)
                schedule.run_count += 1

                event = AgentEvent(
                    event_id=str(uuid7()),
                    event_type=schedule.event_type,
                    payload={
                        **schedule.payload_template,
                        "schedule_id": schedule.schedule_id,
                        "schedule_name": schedule.name,
                        "run_count": schedule.run_count,
                    },
                    source=f"cron:{schedule.name}",
                )

                logger.info(
                    f"CronScheduler firing event for schedule '{schedule.name}' (run #{schedule.run_count})"
                )

                if self._event_loop_ref:
                    create_background_task(
                        self._event_loop_ref.handle_event(event), f"cron-event-{event.event_id}"
                    )
                else:
                    logger.warning(
                        f"CronScheduler no EventDrivenLoop attached for schedule '{schedule.name}'"
                    )

            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception(f"CronScheduler error in schedule '{schedule.name}'")
                await asyncio.sleep(5)


class SystemUpdateRegistry:
    def __init__(self):
        self._updates = deque(maxlen=1000)

    def record(self, update: SystemUpdate):
        self._updates.append(update)
        logger.info(
            f"SystemUpdateRegistry recorded update '{update.update_type}' for event {update.event_id}"
        )

    def get_recent(self, limit: int = 50) -> List[SystemUpdate]:
        return list(reversed(list(self._updates)[-limit:]))

    def get_by_event(self, event_id: str) -> List[SystemUpdate]:
        return [u for u in self._updates if u.event_id == event_id]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self._updates)
        successful = sum(1 for u in self._updates if u.success)
        return {
            "total_updates": total,
            "successful": successful,
            "failed": total - successful,
            "success_rate": round(successful / total, 3) if total > 0 else 0.0,
        }


class EventDrivenLoop:
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._event_queue: asyncio.Queue[AgentEvent] = asyncio.Queue(maxsize=1000)
        self._processed_events = deque(maxlen=1000)
        self._update_registry = SystemUpdateRegistry()
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None

    def register_handler(self, handler: EventHandler):
        if handler.event_type not in self._handlers:
            self._handlers[handler.event_type] = []
        self._handlers[handler.event_type].append(handler)
        logger.info(
            f"EventDrivenLoop registered handler for {handler.event_type.value} {handler.description}"
        )

    async def emit_event(self, event: AgentEvent):
        self._event_queue.put_nowait(event)
        logger.info(f"EventDrivenLoop queued event {event.event_id} ({event.event_type.value})")

    async def handle_event(self, event: AgentEvent) -> Optional[str]:
        handlers = self._handlers.get(event.event_type, [])
        if not handlers:
            logger.debug(f"EventDrivenLoop no handlers for {event.event_type.value}")
            return None

        results = []
        for handler in handlers:
            if not handler.enabled:
                continue
            try:
                result = await handler.handler(event)
                if result:
                    results.append(result)
                    update = SystemUpdate(
                        update_id=str(uuid7()),
                        event_id=event.event_id,
                        update_type=handler.event_type.value,
                        description=f"Handler '{handler.description}' processed event successfully",
                        success=True,
                    )
                    self._update_registry.record(update)
            except Exception as e:
                logger.exception(f"EventDrivenLoop handler '{handler.description}' failed")
                update = SystemUpdate(
                    update_id=str(uuid7()),
                    event_id=event.event_id,
                    update_type=handler.event_type.value,
                    description=f"Handler '{handler.description}' failed: {str(e)[:200]}",
                    success=False,
                )
                self._update_registry.record(update)

        event.processed = True
        event.processing_result = "; ".join(results) if results else None
        self._processed_events.append(event)
        return event.processing_result

    async def start_worker(self):
        self._running = True
        self._worker_task = asyncio.create_task(self._worker_loop(), name="event_driven_worker")
        logger.info("EventDrivenLoop worker started")

    async def stop_worker(self):
        self._running = False
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
        logger.info("EventDrivenLoop worker stopped")

    async def _worker_loop(self):
        while self._running:
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self.handle_event(event)
                self._event_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception:
                logger.exception("EventDrivenLoop worker error")

    def get_stats(self) -> Dict[str, Any]:
        return {
            "queue_size": self._event_queue.qsize(),
            "processed_events": len(self._processed_events),
            "registered_event_types": list(self._handlers.keys()),
            "system_updates": self._update_registry.get_stats(),
            "running": self._running,
        }

    def get_recent_events(self, limit: int = 20) -> List[Dict]:
        events = list(reversed(list(self._processed_events)[-limit:]))
        return [
            {
                "event_id": e.event_id,
                "event_type": e.event_type.value,
                "source": e.source,
                "created_at": e.created_at.isoformat(),
                "processed": e.processed,
                "result": e.processing_result,
                "error": e.error,
            }
            for e in events
        ]

    @property
    def update_registry(self) -> SystemUpdateRegistry:
        return self._update_registry


async def _handle_system_heartbeat(event: AgentEvent) -> Optional[str]:
    logger.info(f"EventDrivenLoop heartbeat ping from {event.source}")
    return "Heartbeat processed"


async def _index_uploaded_document(doc_id: str, user_id: str, superseded_document_id: str):
    from src.clients.knowledge import knowledge_client

    system_ingest = not bool(user_id)
    requester_id = user_id or "platform-system"
    if superseded_document_id:
        await knowledge_client.delete_document(superseded_document_id, requester_id, system_ingest)
    return await knowledge_client.ingest_document(doc_id, requester_id, system_ingest)


async def _handle_document_uploaded(event: AgentEvent) -> Optional[str]:
    doc_id = event.payload.get("document_id")
    user_id = event.payload.get("user_id", "")
    superseded_document_id = event.payload.get("superseded_document_id", "")
    if not doc_id:
        return None
    logger.info(f"EventDrivenLoop document uploaded event for doc_id={doc_id}")

    async def _run_ingest():
        try:
            result = await _index_uploaded_document(doc_id, user_id, superseded_document_id)
            logger.info(
                f"Auto-ingest completed doc_id={doc_id} chunks={result.get('chunks', 0)} method={result.get('extraction_method')}"
            )
        except Exception:
            logger.exception(f"Auto-ingest failed for doc_id={doc_id}")

    create_background_task(_run_ingest(), f"auto-ingest-{doc_id}")
    return f"Document {doc_id} queued for ingestion"


async def _handle_user_query_event(event: AgentEvent) -> Optional[str]:
    query = event.payload.get("query", "")
    user_id = event.payload.get("user_id", "")
    logger.debug(f"EventDrivenLoop user query event from user={user_id} query_chars={len(query)}")
    return f"User query event recorded for user {user_id}"


event_driven_loop = EventDrivenLoop()
cron_scheduler = CronScheduler()
cron_scheduler.set_event_loop(event_driven_loop)

event_driven_loop.register_handler(
    EventHandler(
        event_type=EventType.SYSTEM_HEARTBEAT,
        handler=_handle_system_heartbeat,
        description="System heartbeat health check",
    )
)
event_driven_loop.register_handler(
    EventHandler(
        event_type=EventType.DOCUMENT_UPLOADED,
        handler=_handle_document_uploaded,
        description="Document upload indexing verification",
    )
)
event_driven_loop.register_handler(
    EventHandler(
        event_type=EventType.USER_QUERY,
        handler=_handle_user_query_event,
        description="User query event logging for trace analysis",
    )
)

_heartbeat_schedule = CronSchedule(
    schedule_id="heartbeat_5min",
    name="System Heartbeat",
    cron_expression="*/5 * * * *",
    interval_seconds=300,
    event_type=EventType.SYSTEM_HEARTBEAT,
    payload_template={},
)
cron_scheduler.register(_heartbeat_schedule)
