from functools import lru_cache

from pymongo import MongoClient

from src.core.configuration import settings


@lru_cache(maxsize=1)
def job_event_policy():
    client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        document = client[settings.TESTING_DB_NAME].runtime_policies.find_one(
            {"_id": "job_events"}, {"_id": 0, "values": 1}
        )
    finally:
        client.close()
    if not isinstance(document, dict) or not isinstance(document.get("values"), dict):
        raise RuntimeError("Thiếu chính sách tác vụ nền")
    return document["values"]


def job_event_permissions():
    return {
        event: tuple(permissions)
        for event, permissions in job_event_policy().get("permissions", {}).items()
        if isinstance(event, str) and isinstance(permissions, list)
    }


def allowed_job_events():
    return set(job_event_permissions())
