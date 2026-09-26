from datetime import datetime, timezone
from uuid import uuid4

from src.memory.policy import trusted_outcome
from src.repositories.memory import memory_repository
from src.runtime.models import VeriqRunState


class LongTermMemory:
    async def list(self, project_id: str, limit: int = 20):
        return await memory_repository.list_long_term(project_id, limit)

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
        await memory_repository.record_long_term(state.run_id, value)
        return value


long_term_memory = LongTermMemory()
