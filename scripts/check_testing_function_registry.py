import sys
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TESTING_ROOT = ROOT / "backend" / "testing" if (ROOT / "backend" / "testing").exists() else ROOT
sys.path.insert(0, str(TESTING_ROOT))


def main():
    from src.core.auth import PROJECT_PERMISSIONS
    from src.core.function_ids import FUNCTION_IDS
    from src.main import app

    failures = []
    functions = {}
    excluded = {"health", "ready", "metrics_endpoint"}
    for route in app.routes:
        if not getattr(route, "include_in_schema", False):
            continue
        name = getattr(route.endpoint, "__name__", "")
        if name and name not in excluded and not name.startswith("internal_") and "/noi-bo/" not in route.path:
            functions[name] = route
            if name not in FUNCTION_IDS:
                failures.append(f"route without function ID: {','.join(route.methods)} {route.path}::{name}")
    for name, ids in FUNCTION_IDS.items():
        if len(ids) != len(set(ids)):
            failures.append(f"duplicate function ID on endpoint {name}")
    operation_ids = defaultdict(list)
    for route in app.routes:
        if not getattr(route, "include_in_schema", False) or getattr(route.endpoint, "__name__", "") in excluded or "/noi-bo/" in route.path:
            continue
        name = getattr(route.endpoint, "__name__", "")
        ids = (getattr(route, "openapi_extra", None) or {}).get("x-function-ids", [])
        if not ids:
            failures.append(f"OpenAPI route without x-function-ids: {','.join(route.methods)} {route.path}")
        for function_id in ids:
            operation_ids[function_id].append(f"{','.join(route.methods)} {route.path}")
    prefixes = {
        "STR": "teststrategy.", "TAN": "testcondition.", "MON": "testmonitor.",
        "TSR": "teststatusreport.", "TCP": "testcompletion.", "RVS": "reviewsession.",
        "MET": "measurement.", "PQE": "qualityevaluation.", "RCA": "causalanalysis.",
        "ENVINC": "environmentincident.",
    }
    for prefix, permission_prefix in prefixes.items():
        if any(key.startswith(f"{prefix}-") for key in operation_ids) and not any(permission.startswith(permission_prefix) for permission in PROJECT_PERMISSIONS):
            failures.append(f"function family {prefix} has no permission family {permission_prefix}")
    if failures:
        print("\n".join(sorted(set(failures))))
        raise SystemExit(1)
    print(f"validated {len(functions)} routes and {len(operation_ids)} function IDs")


if __name__ == "__main__":
    main()
