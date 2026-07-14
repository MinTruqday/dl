from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional

import redis.asyncio as aioredis
from loguru import logger

from src.core.infrastructure.configuration import settings

_BANK_TTL_SECONDS = 7200

MemoryCategory = Literal["task_fact", "env_fact", "path", "bug", "perf", "attempt"]

@dataclass
class MemoryEntry:
    id: str
    content: str
    category: MemoryCategory
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    access_count: int = 0


@dataclass
class MemoryBank:
    session_id: str
    status: str = ""
    knowledge: List[MemoryEntry] = field(default_factory=list)
    procedural: List[MemoryEntry] = field(default_factory=list)


def _bank_key(session_id: str) -> str:
    return f"proactive_bank:{session_id}"


def _serialize_entry(entry: MemoryEntry) -> Dict:
    return asdict(entry)


def _deserialize_entry(data: Dict) -> MemoryEntry:
    return MemoryEntry(
        id=data["id"],
        content=data["content"],
        category=data.get("category", "task_fact"),
        created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
        access_count=data.get("access_count", 0),
    )


class ProactiveMemoryBank:
    """
    <module_purpose>
    <purpose>Manages the structured Memory Bank for the Proactive Memory Agent using Redis.</purpose>
    <design>
    Bank structure per session:
      status     — private progress field, visible only to memory agent
      knowledge  — stable facts: task requirements, env facts, paths, configs
      procedural — attempt records: failed commands, bug diagnoses, successful fixes
    </design>
    </module_purpose>
    <contract>
    - Precondition: Redis reachable via REDIS_URI.
    - Postcondition: All mutations are atomic writes with TTL refresh.
    - Error Handling: All Redis failures are caught and logged; methods degrade gracefully.
    </contract>
    """

    def __init__(self) -> None:
        self._redis: Optional[aioredis.Redis] = None

    def _client(self) -> Optional[aioredis.Redis]:
        if self._redis is None:
            try:
                self._redis = aioredis.from_url(
                    settings.REDIS_URI, decode_responses=True
                )
            except Exception:
                logger.exception("ProactiveMemoryBank Redis client initialization failed")
        return self._redis

    async def _load(self, session_id: str) -> MemoryBank:
        client = self._client()
        if not client:
            return MemoryBank(session_id=session_id)
        try:
            raw = await client.get(_bank_key(session_id))
            if not raw:
                return MemoryBank(session_id=session_id)
            data = json.loads(raw)
            return MemoryBank(
                session_id=session_id,
                status=data.get("status", ""),
                knowledge=[_deserialize_entry(e) for e in data.get("knowledge", [])],
                procedural=[_deserialize_entry(e) for e in data.get("procedural", [])],
            )
        except Exception:
            logger.exception(f"ProactiveMemoryBank failed to load bank for session={session_id}")
            return MemoryBank(session_id=session_id)

    async def _persist(self, bank: MemoryBank) -> None:
        client = self._client()
        if not client:
            return
        try:
            payload = json.dumps(
                {
                    "status": bank.status,
                    "knowledge": [_serialize_entry(e) for e in bank.knowledge],
                    "procedural": [_serialize_entry(e) for e in bank.procedural],
                },
                ensure_ascii=False,
            )
            await client.setex(_bank_key(bank.session_id), _BANK_TTL_SECONDS, payload)
        except Exception:
            logger.exception(f"ProactiveMemoryBank failed to persist bank for session={bank.session_id}")

    async def get_bank(self, session_id: str) -> MemoryBank:
        return await self._load(session_id)

    async def update_status(self, session_id: str, status: str) -> None:
        bank = await self._load(session_id)
        bank.status = status
        await self._persist(bank)
        logger.info(f"ProactiveMemoryBank status updated for session={session_id}")

    async def save_knowledge(
        self,
        session_id: str,
        entry_id: str,
        content: str,
        category: MemoryCategory = "task_fact",
    ) -> None:
        bank = await self._load(session_id)
        existing_ids = {e.id for e in bank.knowledge}
        if entry_id in existing_ids:
            for e in bank.knowledge:
                if e.id == entry_id:
                    e.content = content
                    e.category = category
                    e.access_count += 1
                    break
        else:
            bank.knowledge.append(
                MemoryEntry(id=entry_id, content=content, category=category)
            )
        await self._persist(bank)
        logger.info(f"ProactiveMemoryBank knowledge saved id={entry_id} session={session_id}")

    async def save_procedural(
        self,
        session_id: str,
        entry_id: str,
        content: str,
        category: MemoryCategory = "attempt",
    ) -> None:
        bank = await self._load(session_id)
        existing_ids = {e.id for e in bank.procedural}
        if entry_id in existing_ids:
            for e in bank.procedural:
                if e.id == entry_id:
                    e.content = content
                    e.category = category
                    e.access_count += 1
                    break
        else:
            bank.procedural.append(
                MemoryEntry(id=entry_id, content=content, category=category)
            )
        await self._persist(bank)
        logger.info(f"ProactiveMemoryBank procedural saved id={entry_id} session={session_id}")

    async def delete_entry(self, session_id: str, entry_id: str) -> None:
        bank = await self._load(session_id)
        bank.knowledge = [e for e in bank.knowledge if e.id != entry_id]
        bank.procedural = [e for e in bank.procedural if e.id != entry_id]
        await self._persist(bank)
        logger.info(f"ProactiveMemoryBank entry deleted id={entry_id} session={session_id}")

    async def clear_bank(self, session_id: str) -> None:
        client = self._client()
        if not client:
            return
        try:
            await client.delete(_bank_key(session_id))
            logger.info(f"ProactiveMemoryBank cleared for session={session_id}")
        except Exception:
            logger.exception(f"ProactiveMemoryBank failed to clear session={session_id}")

    def format_bank_snapshot(self, bank: MemoryBank) -> str:
        parts: List[str] = []

        if bank.knowledge:
            parts.append("[KNOWLEDGE]")
            for e in bank.knowledge:
                parts.append(f"  [{e.id}] ({e.category}) {e.content}")

        if bank.procedural:
            parts.append("[PROCEDURAL]")
            for e in bank.procedural:
                parts.append(f"  [{e.id}] ({e.category}) {e.content}")

        if not parts:
            return "(empty bank)"

        return "\n".join(parts)


proactive_memory_bank = ProactiveMemoryBank()
