import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def storage_policy() -> dict:
    path = Path(__file__).resolve().parents[1] / "policies" / "storage_policy.json"
    return json.loads(path.read_text(encoding="utf-8"))


def object_prefixes(owner_id: str) -> tuple[str, ...]:
    return tuple(
        value.format(owner_id=owner_id)
        for value in storage_policy()["object_prefixes"]
    )
