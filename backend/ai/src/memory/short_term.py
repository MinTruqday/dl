from datetime import datetime, timezone

from src.repositories.memory import memory_repository
from src.schemas.agent import VeriqRunState


class RunStore:
    async def save(self, state: VeriqRunState):
        state.updated_at = datetime.now(timezone.utc)
        payload = state.model_dump(mode="python")
        payload["_id"] = payload.pop("run_id")
        await memory_repository.save_run(payload)

    async def get(self, run_id: str, project_id: str | None = None):
        payload = await memory_repository.find_run(run_id, project_id)
        if not payload:
            return None
        payload["run_id"] = payload.pop("_id")
        return VeriqRunState(**payload)


run_store = RunStore()
