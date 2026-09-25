from datetime import datetime, timezone
from uuid import uuid4

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.memory.policy import trusted_outcome
from src.runtime.models import VeriqRunState


class LongTermMemory:
    @property
    def collection(self):
        return database.mongodb[settings.AI_DB_NAME].long_term_memory

    async def list(self, project_id: str, limit: int = 20):
        cursor = self.collection.find({"project_id": project_id, "trusted": True}).sort(
            "created_at", -1
        )
        return await cursor.to_list(length=limit)

    async def record_verified(self, state: VeriqRunState):
        if not trusted_outcome(state):
            return None
        value = {
            "_id": f"MEM-{uuid4().hex}",
            "project_id": state.project_id,
            "run_id": state.run_id,
            "objective": state.objective,
            "intent": state.intent,
            "proposal": state.proposal,
            "approval_decision": state.approval_decision,
            "evidence_refs": state.evidence_refs,
            "trusted": True,
            "created_at": datetime.now(timezone.utc),
        }
        await self.collection.update_one(
            {"run_id": state.run_id},
            {"$setOnInsert": value},
            upsert=True,
        )
        return value


long_term_memory = LongTermMemory()
