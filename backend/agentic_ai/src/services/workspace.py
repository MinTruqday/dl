from datetime import datetime, timezone

from src.core.infrastructure.configuration import settings
from src.core.infrastructure.database import database


MODE_DIRECTIVES = {
    "chat": "",
    "work": "Create a verifiable plan then execute each step and report only observed status",
    "goal": "Maintain the objective across turns divide it into measurable steps and finish only after verification",
    "learn": "Teach incrementally check understanding adapt difficulty and let the learner attempt before giving a complete answer",
    "plan": "Create an ordered dependency aware plan with completion criteria and risks without executing tools",
}


class WorkspaceService:
    @staticmethod
    async def start(
        session_id: str, user_id: str, mode: str, objective: str, approval_policy: str
    ) -> None:
        if not session_id or mode == "chat":
            return
        now = datetime.now(timezone.utc)
        await database.mongodb[settings.AGENTIC_AI_DB_NAME].ai_workspaces.update_one(
            {"_id": session_id, "user_id": user_id},
            {
                "$set": {
                    "mode": mode,
                    "last_request": objective,
                    "approval_policy": approval_policy,
                    "status": "planning" if mode == "plan" else "running",
                    "updated_at": now,
                },
                "$setOnInsert": {"created_at": now, "objective": objective, "steps": []},
                "$push": {
                    "requests": {
                        "$each": [{"content": objective, "created_at": now}],
                        "$slice": -50,
                    }
                },
            },
            upsert=True,
        )

    @staticmethod
    async def save_plan(
        session_id: str, user_id: str, steps: list[dict], status: str = "planned"
    ) -> None:
        if not session_id:
            return
        await database.mongodb[settings.AGENTIC_AI_DB_NAME].ai_workspaces.update_one(
            {"_id": session_id, "user_id": user_id},
            {"$set": {"steps": steps, "status": status, "updated_at": datetime.now(timezone.utc)}},
        )

    @staticmethod
    async def update_steps(session_id: str, user_id: str, task_status: dict[str, str]) -> None:
        if not session_id or not task_status:
            return
        collection = database.mongodb[settings.AGENTIC_AI_DB_NAME].ai_workspaces
        row = await collection.find_one({"_id": session_id, "user_id": user_id}, {"steps": 1})
        if not row:
            return
        normalized_status = {str(key): value for key, value in task_status.items()}
        steps = [
            {
                **step,
                "status": normalized_status.get(str(step.get("id")), step.get("status", "pending")),
            }
            for step in row.get("steps", [])
        ]
        await collection.update_one(
            {"_id": session_id, "user_id": user_id},
            {"$set": {"steps": steps, "updated_at": datetime.now(timezone.utc)}},
        )

    @staticmethod
    async def finish(session_id: str, user_id: str, mode: str, success: bool) -> None:
        if not session_id or mode == "chat":
            return
        if mode == "plan" and success:
            status = "planned"
        else:
            status = "active" if mode in {"goal", "learn"} and success else "completed"
        if not success:
            status = "failed"
        await database.mongodb[settings.AGENTIC_AI_DB_NAME].ai_workspaces.update_one(
            {"_id": session_id, "user_id": user_id},
            {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        )

    @staticmethod
    async def get(session_id: str, user_id: str):
        return await database.mongodb[settings.AGENTIC_AI_DB_NAME].ai_workspaces.find_one(
            {"_id": session_id, "user_id": user_id}
        )

    @staticmethod
    async def set_status(session_id: str, user_id: str, status: str) -> None:
        await database.mongodb[settings.AGENTIC_AI_DB_NAME].ai_workspaces.update_one(
            {"_id": session_id, "user_id": user_id},
            {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        )


workspace = WorkspaceService()
