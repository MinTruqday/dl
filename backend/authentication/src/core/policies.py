import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def platform_policy() -> dict:
    path = Path(__file__).resolve().parents[1] / "policies" / "platform.json"
    return json.loads(path.read_text(encoding="utf-8"))
