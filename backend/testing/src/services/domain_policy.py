import json
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def domain_policies():
    path = Path(__file__).resolve().parents[1] / "policies" / "analysis_policy.json"
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def domain_policy(name):
    return domain_policies()[name]
