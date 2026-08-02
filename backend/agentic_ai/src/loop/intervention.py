import asyncio
import json
from uuid6 import uuid7
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

from loguru import logger
from src.utils.background import create_background_task

InterventionStatus = Literal[
    "PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
    "CORRECTED",
    "EXPIRED",
]

RiskLevel = Literal["low", "medium", "high", "critical"]

@dataclass
class InterventionRequest:
    intervention_id: str
    session_id: str
    user_id: str
    action_type: str
    description: str
    proposed_action: str
    risk_level: RiskLevel
    status: InterventionStatus = "PENDING_APPROVAL"
    human_feedback: Optional[str] = None
    correction: Optional[str] = None
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = None

@dataclass
class InterventionAuditEntry:
    intervention_id: str
    session_id: str
    user_id: str
    action_type: str
    risk_level: RiskLevel
    status: InterventionStatus
    human_feedback: Optional[str]
    correction: Optional[str]
    requested_at: datetime
    resolved_at: Optional[datetime]
    duration_seconds: Optional[float]

class InterventionHarness:
    def __init__(self):
        self._pending: Dict[str, InterventionRequest] = {}
        self._approved: Dict[str, InterventionRequest] = {}
        self._audit_log: List[InterventionAuditEntry] = []
        self._redis_client = None
        self._default_ttl_seconds = 300

    def _get_redis(self):
        if self._redis_client is None:
            try:
                import redis.asyncio as aioredis
                from src.core.infrastructure.configuration import settings
                self._redis_client = aioredis.from_url(
                    settings.REDIS_URI, decode_responses=True
                )
            except Exception:
                logger.exception("Intervention tracking system Redis connection error")
        return self._redis_client

    async def request_approval(
        self,
        session_id: str,
        user_id: str,
        action_type: str,
        description: str,
        proposed_action: str,
        risk_level: RiskLevel = "medium",
        ttl_seconds: Optional[int] = None,
    ) -> InterventionRequest:
        intervention_id = str(uuid7())
        request = InterventionRequest(
            intervention_id=intervention_id,
            session_id=session_id,
            user_id=user_id,
            action_type=action_type,
            description=description,
            proposed_action=proposed_action,
            risk_level=risk_level,
        )
        self._pending[intervention_id] = request

        redis = self._get_redis()
        ttl = ttl_seconds or self._default_ttl_seconds
        if redis:
            key = f"intervention:{session_id}:{intervention_id}"
            try:
                payload = {
                    "intervention_id": intervention_id,
                    "session_id": session_id,
                    "user_id": user_id,
                    "action_type": action_type,
                    "description": description,
                    "proposed_action": proposed_action,
                    "risk_level": risk_level,
                    "status": "PENDING_APPROVAL",
                }
                await redis.setex(key, ttl, json.dumps(payload, ensure_ascii=False))
            except Exception:
                logger.exception("Error persisting intervention request to Redis layer")
        create_background_task(
            self._auto_expire(intervention_id, ttl),
            f"intervention-expire-{intervention_id}",
        )

        logger.warning(
            f"Intervention approval requested: action={action_type}, risk={risk_level}, session={session_id}"
        )
        return request

    async def _auto_expire(self, intervention_id: str, delay: int):
        await asyncio.sleep(delay)
        request = self._pending.get(intervention_id)
        if request and request.status == "PENDING_APPROVAL":
            request.status = "EXPIRED"
            request.resolved_at = datetime.now(timezone.utc)
            self._pending.pop(intervention_id, None)
            self._record_audit(request)
            logger.warning(
                f"Intervention request {intervention_id} expired due to timeout"
            )

    async def record_feedback(
        self,
        intervention_id: str,
        status: Literal["APPROVED", "REJECTED", "CORRECTED"],
        human_feedback: Optional[str] = None,
        correction: Optional[str] = None,
    ) -> Optional[InterventionRequest]:
        request = self._pending.get(intervention_id)
        if not request:
            logger.warning(f"Intervention request {intervention_id} not found in pending queue")
            return None

        request.status = status
        request.human_feedback = human_feedback
        request.correction = correction
        request.resolved_at = datetime.now(timezone.utc)

        self._pending.pop(intervention_id, None)
        if status == "APPROVED":
            self._approved[intervention_id] = request
        self._record_audit(request)

        redis = self._get_redis()
        if redis:
            key = f"intervention:{request.session_id}:{intervention_id}"
            try:
                await redis.delete(key)
                if status == "APPROVED":
                    await redis.setex(
                        f"intervention:approved:{intervention_id}",
                        self._default_ttl_seconds,
                        json.dumps(
                            {
                                "intervention_id": intervention_id,
                                "session_id": request.session_id,
                                "user_id": request.user_id,
                                "action_type": request.action_type,
                            },
                            ensure_ascii=False,
                        ),
                    )
            except Exception:
                logger.exception("Error deleting intervention request from Redis cache")

        logger.info(
            f"Intervention feedback recorded: id={intervention_id}, status={status}"
        )
        return request

    async def consume_approval(
        self,
        intervention_id: str,
        session_id: str,
        user_id: str,
        action_type: str,
    ) -> bool:
        request = self._approved.get(intervention_id)
        if request:
            matches = (
                request.session_id == session_id
                and request.user_id == user_id
                and request.action_type == action_type
            )
            if not matches:
                return False
            self._approved.pop(intervention_id, None)
            redis = self._get_redis()
            if redis:
                try:
                    await redis.delete(f"intervention:approved:{intervention_id}")
                except Exception:
                    logger.exception("Approved intervention cleanup failed")
            return True

        redis = self._get_redis()
        if not redis:
            return False
        try:
            key = f"intervention:approved:{intervention_id}"
            raw = await redis.get(key)
            if not raw:
                return False
            data = json.loads(raw)
            matches = (
                data.get("session_id") == session_id
                and data.get("user_id") == user_id
                and data.get("action_type") == action_type
            )
            if not matches:
                return False
            await redis.delete(key)
            return True
        except Exception:
            logger.exception("Approved intervention lookup failed")
            return False

    async def wait_for_approval(
        self,
        intervention_id: str,
        session_id: str,
        user_id: str,
        action_type: str,
        timeout_seconds: int = 300,
    ) -> bool:
        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout_seconds
        while loop.time() < deadline:
            if await self.consume_approval(
                intervention_id,
                session_id,
                user_id,
                action_type,
            ):
                return True
            if not await self.check_pending(intervention_id):
                return False
            await asyncio.sleep(0.5)
        return False

    def _record_audit(self, request: InterventionRequest):
        duration = None
        if request.resolved_at:
            duration = round(
                (request.resolved_at - request.requested_at).total_seconds(), 2
            )
        entry = InterventionAuditEntry(
            intervention_id=request.intervention_id,
            session_id=request.session_id,
            user_id=request.user_id,
            action_type=request.action_type,
            risk_level=request.risk_level,
            status=request.status,
            human_feedback=request.human_feedback,
            correction=request.correction,
            requested_at=request.requested_at,
            resolved_at=request.resolved_at,
            duration_seconds=duration,
        )
        self._audit_log.append(entry)

    async def check_pending(
        self,
        intervention_id: str,
    ) -> Optional[InterventionRequest]:
        request = self._pending.get(intervention_id)
        if request:
            return request

        redis = self._get_redis()
        if not redis:
            return None

        try:
            key_pattern = f"intervention:*:{intervention_id}"
            keys = await redis.keys(key_pattern)
            if keys:
                raw = await redis.get(keys[0])
                if raw:
                    data = json.loads(raw)
                    request = InterventionRequest(
                        intervention_id=data["intervention_id"],
                        session_id=data["session_id"],
                        user_id=data["user_id"],
                        action_type=data["action_type"],
                        description=data.get("description", ""),
                        proposed_action=data.get("proposed_action", ""),
                        risk_level=data.get("risk_level", "medium"),
                        status=data.get("status", "PENDING_APPROVAL"),
                    )
                    self._pending[intervention_id] = request
                    return request
        except Exception:
            logger.exception("Error checking intervention status from Redis")
        return None

    async def get_pending_by_session(self, session_id: str) -> List[InterventionRequest]:
        requests = [
            r for r in self._pending.values()
            if r.session_id == session_id and r.status == "PENDING_APPROVAL"
        ]
        redis = self._get_redis()
        if redis:
            try:
                async for key in redis.scan_iter(
                    match=f"intervention:{session_id}:*",
                    count=100,
                ):
                    raw = await redis.get(key)
                    if not raw:
                        continue
                    data = json.loads(raw)
                    intervention_id = data.get("intervention_id", "")
                    if not intervention_id or intervention_id in self._pending:
                        continue
                    request = InterventionRequest(
                        intervention_id=intervention_id,
                        session_id=data["session_id"],
                        user_id=data["user_id"],
                        action_type=data["action_type"],
                        description=data.get("description", ""),
                        proposed_action=data.get("proposed_action", ""),
                        risk_level=data.get("risk_level", "medium"),
                        status=data.get("status", "PENDING_APPROVAL"),
                    )
                    self._pending[intervention_id] = request
                    requests.append(request)
            except Exception:
                logger.exception("Pending intervention lookup failed")
        return requests

    def get_audit_log(self, session_id: Optional[str] = None) -> List[InterventionAuditEntry]:
        if session_id:
            return [e for e in self._audit_log if e.session_id == session_id]
        return list(self._audit_log)

    def get_session_summary(self, session_id: str) -> Dict:
        entries = self.get_audit_log(session_id)
        if not entries:
            return {"session_id": session_id, "total": 0}
        breakdown: Dict[str, int] = {}
        for entry in entries:
            breakdown[entry.status] = breakdown.get(entry.status, 0) + 1
        avg_duration = None
        durations = [e.duration_seconds for e in entries if e.duration_seconds is not None]
        if durations:
            avg_duration = round(sum(durations) / len(durations), 2)
        return {
            "session_id": session_id,
            "total": len(entries),
            "breakdown": breakdown,
            "avg_resolution_seconds": avg_duration,
        }

intervention = InterventionHarness()
