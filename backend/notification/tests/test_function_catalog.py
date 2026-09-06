import re

from src.core.function_ids import FUNCTION_IDS
from src.main import app


def test_notification_routes_have_function_ids():
    missing = []
    for route in app.routes:
        if not route.path.startswith("/thong-bao") or not route.include_in_schema:
            continue
        if route.endpoint.__name__ == "delete_announcement":
            continue
        if not (getattr(route, "openapi_extra", None) or {}).get("x-function-ids"):
            missing.append(f"{sorted(route.methods or [])} {route.path}")
    assert missing == []


def test_function_ids_are_well_formed():
    values = {value for identifiers in FUNCTION_IDS.values() for value in identifiers}
    assert all(
        re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+", value)
        for value in values
    )


if __name__ == "__main__":
    test_notification_routes_have_function_ids()
    test_function_ids_are_well_formed()
    print("notification function catalog test passed")
