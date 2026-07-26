from src.core.infrastructure.mongo import mongo

class PomodoroRepository:
    @classmethod
    async def insert_session(cls, *args, **kwargs):
        return await mongo.insert_one("pomodoro_sessions", *args, **kwargs)
