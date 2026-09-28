from functools import lru_cache

from pymongo import MongoClient

from src.core.infrastructure.configuration import settings


@lru_cache(maxsize=1)
def storage_policy() -> dict:
    client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        value = client[settings.CLOUD_DB_NAME].runtime_policies.find_one(
            {"_id": "storage_policy"}, {"_id": 0, "values": 1}
        )
    finally:
        client.close()
    if not isinstance(value, dict) or not isinstance(value.get("values"), dict):
        raise RuntimeError("Thiếu chính sách lưu trữ")
    return value["values"]


def object_prefixes(owner_id: str) -> tuple[str, ...]:
    return tuple(
        value.format(owner_id=owner_id)
        for value in storage_policy()["object_prefixes"]
    )
