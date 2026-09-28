from functools import lru_cache
from collections.abc import Mapping

from pymongo import MongoClient

from src.core.infrastructure.configuration import settings


@lru_cache(maxsize=1)
def platform_policy() -> dict:
    client = MongoClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        value = client[settings.AUTHENTICATION_DB_NAME].system_configs.find_one(
            {"type": "platform_policy"}, {"_id": 0, "values": 1}
        )
    finally:
        client.close()
    if not isinstance(value, dict) or not isinstance(value.get("values"), dict):
        raise RuntimeError("Thiếu chính sách vận hành nền tảng")
    return value["values"]


class PolicySection(Mapping):
    def __init__(self, name: str):
        self.name = name

    def _values(self):
        value = platform_policy().get(self.name)
        if not isinstance(value, dict):
            raise RuntimeError(f"Thiếu phần chính sách {self.name}")
        return value

    def __getitem__(self, key):
        return self._values()[key]

    def __iter__(self):
        return iter(self._values())

    def __len__(self):
        return len(self._values())


def policy_section(name: str) -> PolicySection:
    return PolicySection(name)
