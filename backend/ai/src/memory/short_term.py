from datetime import datetime, timezone

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database
from src.runtime.models import VeriqRunState


class RunStore:
    @property
    def collection(self):
        return database.mongodb[settings.AI_DB_NAME].agent_runs

    async def save(self, state: VeriqRunState):
        state.updated_at = datetime.now(timezone.utc)
        payload = state.model_dump(mode="python")
        payload["_id"] = payload.pop("run_id")
        await self.collection.replace_one({"_id": payload["_id"]}, payload, upsert=True)

    async def get(self, run_id: str, project_id: str | None = None):
        query = {"_id": run_id}
        if project_id:
            query["project_id"] = project_id
        payload = await self.collection.find_one(query)
        if not payload:
            return None
        payload["run_id"] = payload.pop("_id")
        return VeriqRunState(**payload)


run_store = RunStore()
