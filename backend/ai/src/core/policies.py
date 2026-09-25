import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def document_policy() -> dict:
    path = Path(__file__).resolve().parents[1] / "policies" / "document_processing.json"
    return json.loads(path.read_text(encoding="utf-8"))
