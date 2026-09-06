import re

from src.core.function_ids import FUNCTION_IDS, ROUTE_NAME_FUNCTION_IDS
from src.main import app


def test_public_business_routes_have_function_ids():
    missing = []
    for route in app.routes:
        if not route.path.startswith(("/xac-thuc", "/quan-tri")):
            continue
        if route.path.startswith("/xac-thuc/noi-bo"):
            continue
        if not (getattr(route, "openapi_extra", None) or {}).get("x-function-ids"):
            missing.append(f"{sorted(route.methods or [])} {route.path}")
    assert missing == []


def test_function_ids_are_well_formed():
    values = {
        value
        for catalog in (FUNCTION_IDS, ROUTE_NAME_FUNCTION_IDS)
        for identifiers in catalog.values()
        for value in identifiers
    }
    assert values
    assert all(
        re.fullmatch(r"[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+", value)
        for value in values
    )


if __name__ == "__main__":
    test_public_business_routes_have_function_ids()
    test_function_ids_are_well_formed()
    print("authentication function catalog test passed")
